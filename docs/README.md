YADT Spec
===

# Structure

- simplewpml.v1.rng: The markup language spec acting as a intermidate representation between the parse and the render.


# Getting Started

```xml
<?xml version="1.0" encoding="UTF-8"?>
<wp:document xmlns:wp="urn:ns:yadt:simplewpml">
    <wp:page>
        <!-- 标题段落 -->
        <wp:block offsetX="10%" offsetY="5%" width="80%" height="auto">
            <wp:p align="center">
                <wp:run font-family="Arial" color="000000">示例文档标题</wp:run>
            </wp:p>
        </wp:block>

        <!-- 正文段落 -->
        <wp:block offsetX="10%" offsetY="15%" width="80%" height="auto">
            <wp:p align="justify">
                <wp:run>这是一个普通段落，包含一些</wp:run>
                <wp:run color="0000FF">彩色文本</wp:run>
                <wp:run>和一个</wp:run>
                <wp:run>数学公式：</wp:run>
                <wp:math>E = mc^2</wp:math>
            </wp:p>
        </wp:block>

        <!-- 表格 -->
        <wp:block offsetX="10%" offsetY="30%" width="80%" height="auto">
            <wp:table frame="all" rowsep="1" colsep="1">
                <wp:cols>
                    <wp:col colwidth="30%"/>
                    <wp:col colwidth="70%"/>
                </wp:cols>
                <wp:thead>
                    <wp:tr>
                        <wp:td align="center">
                            <wp:p>
                                <wp:run>表头1</wp:run>
                            </wp:p>
                        </wp:td>
                        <wp:td align="center">
                            <wp:p>
                                <wp:run>表头2</wp:run>
                            </wp:p>
                        </wp:td>
                    </wp:tr>
                </wp:thead>
                <wp:tbody>
                    <wp:tr>
                        <wp:td>
                            <wp:p>
                                <wp:run>单元格1</wp:run>
                            </wp:p>
                        </wp:td>
                        <wp:td>
                            <wp:p>
                                <wp:run>单元格2</wp:run>
                            </wp:p>
                        </wp:td>
                    </wp:tr>
                </wp:tbody>
            </wp:table>
        </wp:block>

        <!-- 图片对象 -->
        <wp:block offsetX="10%" offsetY="50%" width="80%" height="auto">
            <wp:object>
                <wp:figure 
                    src="example.png" 
                    width="50%" 
                    height="auto" 
                    caption="示例图片" 
                    title="这是一个示例图片">
                </wp:figure>
            </wp:object>
        </wp:block>

        <!-- 代码块 -->
        <wp:block offsetX="10%" offsetY="70%" width="80%" height="auto">
            <wp:object>
                <wp:codeblock language="python">
                    <wp:codeline number="1">def hello_world():</wp:codeline>
                    <wp:codeline number="2" highlight="true">    print("Hello, World!")</wp:codeline>
                    <wp:codeline number="3">    return None</wp:codeline>
                </wp:codeblock>
            </wp:object>
        </wp:block>
    </wp:page>
</wp:document>
```
