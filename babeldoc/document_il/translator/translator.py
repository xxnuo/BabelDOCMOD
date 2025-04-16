import contextlib
import logging
import threading
import time
import unicodedata
from abc import ABC
from abc import abstractmethod

import openai
from tenacity import retry
from tenacity import retry_if_exception_type
from tenacity import stop_after_attempt
from tenacity import wait_exponential

from babeldoc.document_il.translator.cache import TranslationCache
from babeldoc.document_il.utils.atomic_integer import AtomicInteger

logger = logging.getLogger(__name__)


def remove_control_characters(s):
    return "".join(ch for ch in s if unicodedata.category(ch)[0] != "C")


class RateLimiter:
    def __init__(self, max_qps: int):
        self.max_qps = max_qps
        self.min_interval = 1.0 / max_qps
        self.last_requests = []  # Track last N requests
        self.window_size = max_qps  # Track requests in a sliding window
        self.lock = threading.Lock()

    def wait(self):
        with self.lock:
            now = time.time()

            # Clean up old requests outside the 1-second window
            while self.last_requests and now - self.last_requests[0] > 1.0:
                self.last_requests.pop(0)

            # If we have less than max_qps requests in the last second, allow immediately
            if len(self.last_requests) < self.max_qps:
                self.last_requests.append(now)
                return

            # Otherwise, wait until we can make the next request
            next_time = self.last_requests[0] + 1.0
            if next_time > now:
                time.sleep(next_time - now)
            self.last_requests.pop(0)
            self.last_requests.append(next_time)

    def set_max_qps(self, max_qps):
        self.max_qps = max_qps
        self.min_interval = 1.0 / max_qps
        self.window_size = max_qps


_translate_rate_limiter = RateLimiter(5)


def set_translate_rate_limiter(max_qps):
    _translate_rate_limiter.set_max_qps(max_qps)


class BaseTranslator(ABC):
    # Due to cache limitations, name should be within 20 characters.
    # cache.py: translate_engine = CharField(max_length=20)
    name = "base"
    lang_map = {}

    def __init__(self, lang_in, lang_out, ignore_cache):
        self.ignore_cache = ignore_cache
        lang_in = self.lang_map.get(lang_in.lower(), lang_in)
        lang_out = self.lang_map.get(lang_out.lower(), lang_out)
        self.lang_in = lang_in
        self.lang_out = lang_out

        self.cache = TranslationCache(
            self.name,
            {
                "lang_in": lang_in,
                "lang_out": lang_out,
            },
        )

        self.translate_call_count = 0
        self.translate_cache_call_count = 0

    def __del__(self):
        with contextlib.suppress(Exception):
            logger.info(
                f"{self.name} translate call count: {self.translate_call_count}"
            )
            logger.info(
                f"{self.name} translate cache call count: {self.translate_cache_call_count}",
            )

    def add_cache_impact_parameters(self, k: str, v):
        """
        Add parameters that affect the translation quality to distinguish the translation effects under different parameters.
        :param k: key
        :param v: value
        """
        self.cache.add_params(k, v)

    def translate(self, text, ignore_cache=False, rate_limit_params: dict = None):
        """
        Translate the text, and the other part should call this method.
        :param text: text to translate
        :return: translated text
        """
        self.translate_call_count += 1
        if not (self.ignore_cache or ignore_cache):
            cache = self.cache.get(text)
            if cache is not None:
                self.translate_cache_call_count += 1
                return cache
        _translate_rate_limiter.wait()
        translation = self.do_translate(text, rate_limit_params)
        if not (self.ignore_cache or ignore_cache):
            self.cache.set(text, translation)
        return translation

    def llm_translate(self, text, ignore_cache=False, rate_limit_params: dict = None):
        """
        Translate the text, and the other part should call this method.
        :param text: text to translate
        :return: translated text
        """
        self.translate_call_count += 1
        if not (self.ignore_cache or ignore_cache):
            cache = self.cache.get(text)
            if cache is not None:
                self.translate_cache_call_count += 1
                return cache
        _translate_rate_limiter.wait()
        translation = self.do_llm_translate(text, rate_limit_params)
        if not (self.ignore_cache or ignore_cache):
            self.cache.set(text, translation)
        return translation

    @abstractmethod
    def do_llm_translate(self, text, rate_limit_params: dict = None):
        """
        Actual translate text, override this method
        :param text: text to translate
        :return: translated text
        """
        raise NotImplementedError

    @abstractmethod
    def do_translate(self, text, rate_limit_params: dict = None):
        """
        Actual translate text, override this method
        :param text: text to translate
        :return: translated text
        """
        logger.critical(
            f"Do not call BaseTranslator.do_translate. "
            f"Translator: {self}. "
            f"Text: {text}. ",
        )
        raise NotImplementedError

    def __str__(self):
        return f"{self.name} {self.lang_in} {self.lang_out} {self.model}"

    def get_rich_text_left_placeholder(self, placeholder_id: int):
        return f"<b{placeholder_id}>"

    def get_rich_text_right_placeholder(self, placeholder_id: int):
        return f"</b{placeholder_id}>"

    def get_formular_placeholder(self, placeholder_id: int):
        return self.get_rich_text_left_placeholder(placeholder_id)


class OpenAITranslator(BaseTranslator):
    # https://github.com/openai/openai-python
    name = "openai"

    advanced_lang_map = {
        "en": "英语",
        "en-US": "英语",
        "zh-CN": "简体中文",
        "zh": "简体中文",
        "zh-TW": "繁体中文",
        "ja": "日语",
        "ko": "韩语",
        "ru": "俄语",
        "fr": "法语",
        "de": "德语",
        "it": "意大利语",
        "es": "西班牙语",
    }

    def __init__(
        self,
        lang_in,
        lang_out,
        model,
        base_url=None,
        api_key=None,
        ignore_cache=False,
        qps: int = 200,
        dict_names: list[str] = None,
        temp_dict: dict[str, str] = None,
    ):
        super().__init__(lang_in, lang_out, ignore_cache)
        self.options = {"temperature": 0}  # 随机采样可能会打断公式标记
        self.client = openai.OpenAI(base_url=base_url, api_key=api_key)
        self.add_cache_impact_parameters("temperature", self.options["temperature"])
        self.model = model
        self.add_cache_impact_parameters("model", self.model)
        self.add_cache_impact_parameters("prompt", self.prompt(""))
        self.token_count = AtomicInteger()
        self.prompt_token_count = AtomicInteger()
        self.completion_token_count = AtomicInteger()

        # Advanced features
        self.ignore_cache = ignore_cache
        self.add_cache_impact_parameters("dict_names", dict_names)
        self.add_cache_impact_parameters("temp_dict", temp_dict)
        set_translate_rate_limiter(qps)

        if dict_names:
            from app.api.v2.translator.engines.vocab import MultiVocab
            import app.envs
            import os

            dict_paths = [
                os.path.join(app.envs.LLM_DICT_DIR, f"{dict_name}.xlsx")
                for dict_name in dict_names
            ]
            self.vocab = MultiVocab(dict_paths, temp_dict, self.lang_out)
        else:
            self.vocab = None

    def translate(self, text, ignore_cache=False, rate_limit_params: dict = None, dictionary: dict[str, str] = None):
        """
        Translate the text, and the other part should call this method.
        :param text: text to translate
        :param ignore_cache: whether to ignore cache
        :param rate_limit_params: parameters for rate limiting
        :param dictionary: optional dictionary for term translation
        :return: translated text
        """
        self.translate_call_count += 1
        if not (self.ignore_cache or ignore_cache):
            cache = self.cache.get(text)
            if cache is not None:
                self.translate_cache_call_count += 1
                return cache
        _translate_rate_limiter.wait()

        if dictionary is None:
            dictionary = (
                self.vocab.match_by_lang(text, self.lang_out)
                if self.vocab
                else None
            )

        translation = self.do_translate(text, rate_limit_params, dictionary)
        if not (self.ignore_cache or ignore_cache):
            self.cache.set(text, translation)
        return translation

    @retry(
        retry=retry_if_exception_type(openai.RateLimitError),
        stop=stop_after_attempt(100),
        wait=wait_exponential(multiplier=1, min=1, max=15),
        before_sleep=lambda retry_state: logger.warning(
            f"RateLimitError, retrying in {retry_state.next_action.sleep} seconds... "
            f"(Attempt {retry_state.attempt_number}/100)"
        ),
    )
    def do_translate(self, text, rate_limit_params: dict = None, dictionary: dict[str, str] = None) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            **self.options,
            messages=self.prompt(text, dictionary),
        )
        self.token_count.inc(response.usage.total_tokens)
        self.prompt_token_count.inc(response.usage.prompt_tokens)
        self.completion_token_count.inc(response.usage.completion_tokens)
        return response.choices[0].message.content.strip()

    def prompt(self, text, dictionary: dict[str, str] = None):
        is_auto_lang = self.lang_in == ""
        in_lang_part = (
            "任何" if is_auto_lang else f"{self.advanced_lang_map[self.lang_in]}"
        )
        # 生成非目标语言处理说明
        out_lang_part = (
            f"{self.advanced_lang_map[self.lang_out]}"
            if is_auto_lang
            else f"{self.advanced_lang_map[self.lang_out]}, 源文本中非{self.advanced_lang_map[self.lang_in]}的部分内容直接使用原文作为译文"
        )
        if dictionary:
            dictionary_part = "\n\n参考术语:\n" + "\n".join(
                f"{k}: {v}" for k, v in dictionary.items()
            )
        else:
            dictionary_part = ""
        
        return [
            {
                "role": "system",
                "content": rf"""你是一位专业的多语言法律领域翻译专家. 请遵循以下指南:
1. 翻译原则
- 严格遵循法律用语的专业性和严谨性
- 准确传达法律条款的权利义务关系
- 保持法律术语的规范性和一致性
- 确保译文符合目标语言的法律表述习惯
2. 基本要求
- 严格保持原文的格式,标点和段落结构
- 保留所有数学公式,代码等特殊标记
- 使用权威法律词典和判例中的标准译法
- 在保证法律含义准确的前提下使译文通顺
- 对合同主体,权利义务,期限等关键内容的翻译尤其谨慎
3. 特殊情况处理
- 遇到不确定或多种译法的术语,选择最合适的译法
- 遇到文化差异内容和语气词,使用目标语言的习惯表达
- 遇到短词组或单个词语,如无上下文,选择最常用的译法
- 遇到短文本,如无上下文,选择最常用的译法{dictionary_part}
""",
            },
            {
                "role": "user",
                "content": f";; 将用户在下一行输入的{in_lang_part}内容翻译成{out_lang_part}.仅输出译文,如果是不必要的翻译(例如专有名词、代码、{'{{1}}, 等'}),返回原文.不要解释,不要备注.输入内容:",
            },
            {
                "role": "user",
                "content": text,
            },
        ]

    @retry(
        retry=retry_if_exception_type(openai.RateLimitError),
        stop=stop_after_attempt(100),
        wait=wait_exponential(multiplier=1, min=1, max=15),
        before_sleep=lambda retry_state: logger.warning(
            f"RateLimitError, retrying in {retry_state.next_action.sleep} seconds... "
            f"(Attempt {retry_state.attempt_number}/100)"
        ),
    )
    def do_llm_translate(self, text, rate_limit_params: dict = None, dictionary: dict[str, str] = None):
        if text is None:
            return None

        print(text)

        # if dictionary is None:
        #     dictionary = (
        #         self.vocab.match_by_lang(text, self.lang_out)
        #         if self.vocab
        #         else None
        #     )

        if dictionary:
            dictionary_part = "\n\n参考术语:\n" + "\n".join(
                f"{k}: {v}" for k, v in dictionary.items()
            )
        else:
            dictionary_part = ""
        
        response = self.client.chat.completions.create(
            model=self.model,
            **self.options,
            messages=[
                {
                    "role": "system",
                    "content": rf"""你是一位专业的多语言法律领域翻译专家. 请遵循以下指南:
1. 翻译原则
- 严格遵循法律用语的专业性和严谨性
- 准确传达法律条款的权利义务关系
- 保持法律术语的规范性和一致性
- 确保译文符合目标语言的法律表述习惯
2. 基本要求
- 严格保持原文的格式,标点和段落结构
- 保留所有数学公式,代码等特殊标记
- 使用权威法律词典和判例中的标准译法
- 在保证法律含义准确的前提下使译文通顺
- 对合同主体,权利义务,期限等关键内容的翻译尤其谨慎
3. 特殊情况处理
- 遇到不确定或多种译法的术语,选择最合适的译法
- 遇到文化差异内容和语气词,使用目标语言的习惯表达
- 遇到短词组或单个词语,如无上下文,选择最常用的译法
- 遇到短文本,如无上下文,选择最常用的译法{dictionary_part}
"""
                },
                {
                    "role": "user",
                    "content": text,
                },
            ],
        )
        self.token_count.inc(response.usage.total_tokens)
        self.prompt_token_count.inc(response.usage.prompt_tokens)
        self.completion_token_count.inc(response.usage.completion_tokens)
        return response.choices[0].message.content.strip()

    def get_formular_placeholder(self, placeholder_id: int):
        return "{{v" + str(placeholder_id) + "}}"
        return "{{" + str(placeholder_id) + "}}"

    def get_rich_text_left_placeholder(self, placeholder_id: int):
        return self.get_formular_placeholder(placeholder_id)

    def get_rich_text_right_placeholder(self, placeholder_id: int):
        return self.get_formular_placeholder(placeholder_id + 1)

if __name__ == "__main__":
    translator = OpenAITranslator(
        lang_in="zh-CN",
        lang_out="en-US",
        # model="qwen2-instruct",
        model="Qwen/Qwen2.5-72B-Instruct",
        # base_url="http://127.0.0.1:9997/v1",
        base_url="https://api.siliconflow.cn/v1",
        # api_key="EMPTY",
        api_key="sk-kxyyqvlclkbswvrnzyzjdzxoarunqjunjylvdeutleaxwhoi",
    )
    texts = [
        "与",
        "关于",
        "之",
        "定义",
        "终止",
        "兹此",
        "用途",
        "B",
        "C",
        "G",
        "J",
        "元",
        "啊",
        "软件许可所有权",
        "甲方",
        "乙方",
        "丙方",
        "丁方",
        "我是经过 UFCC 许可认证的。",
        ", You have no permission",
        ", You have no permission {1}",
        "你没有许可 {1}",
    ]
    for text in texts:
        print(
            translator.translate(
                text,
                dictionary={
                    "与": "and",
                    "关于": "about",
                    "之": "of",
                },
            )
        )

    # 测试临时词典