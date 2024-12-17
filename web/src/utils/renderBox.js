import labels from "./labels.json";
import Tesseract from 'tesseract.js';

/**
 * Render prediction boxes and perform OCR
 * @param {CanvasRenderingContext2D} ctx context
 * @param {Array[Object]} boxes boxes array
 */
export const renderBoxes = async (ctx, boxes) => {
  const colors = new Colors();
  
  const timings = {
    ocr: 0,
    translation: 0
  };

  const font = `${Math.max(
    Math.round(Math.max(ctx.canvas.width, ctx.canvas.height) / 40),
    14
  )}px Arial`;
  ctx.font = font;
  ctx.textBaseline = "top";

  // OCR timing start
  const ocrStart = performance.now();
  const ocrPromises = boxes.map(async box => {
    const [x1, y1, width, height] = box.bounding;
    const imageData = ctx.getImageData(x1, y1, width, height);
    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    const tempCtx = canvas.getContext('2d');
    tempCtx.putImageData(imageData, 0, 0);

    try {
      const { data: { text } } = await Tesseract.recognize(canvas);
      return {
        ...box,
        originalText: text.trim()
      };
    } catch(err) {
      console.error('OCR failed:', err);
      return {
        ...box,
        originalText: ''
      };
    }
  });

  let boxesWithText = await Promise.all(ocrPromises);
  timings.ocr = performance.now() - ocrStart;

  const textsToTranslate = boxesWithText
    .map(box => box.originalText)
    .filter(text => text);

  let translations = [];
  if (textsToTranslate.length > 0) {
    const translationStart = performance.now();
    try {
      const response = await fetch('https://api2.immersivetranslate.com/deepl/translate', {
        method: 'POST',
        headers: {
          'content-type': 'application/json',
          'token': 'temp-token-2023'
        },
        body: JSON.stringify({
          text: textsToTranslate,
          source_lang: 'EN',
          target_lang: 'ZH'
        })
      });
      
      const data = await response.json();
      translations = data.translations?.map(t => t.text) || textsToTranslate;
    } catch (err) {
      console.error('Translation failed:', err);
      translations = textsToTranslate;
    }
    timings.translation = performance.now() - translationStart;
  }

  // Add translations back to boxes
  let translationIndex = 0;
  boxesWithText = boxesWithText.map(box => {
    if (box.originalText) {
      return {
        ...box,
        translatedText: translations[translationIndex++]
      };
    }
    return box;
  });

  // Render boxes and translations
  boxesWithText.forEach(box => {
    const color = colors.get(box.label);
    const [x1, y1, width, height] = box.bounding;

    // Draw box
    ctx.strokeStyle = color;
    ctx.lineWidth = Math.max(Math.min(ctx.canvas.width, ctx.canvas.height) / 200, 2.5);
    ctx.strokeRect(x1, y1, width, height);
    ctx.fillStyle = Colors.hexToRgba(color, 0.2);
    ctx.fillRect(x1, y1, width, height);

    // Draw translated text if available
    if (box.translatedText) {
      const fontSize = Math.min(width / 20, height / 6) * 2;
      ctx.font = `${fontSize}px Arial`;
      const lineHeight = fontSize * 1.2;
      
      // Split text into lines
      const maxWidth = width - 4;
      const words = box.translatedText.split(' ');
      const lines = [];
      let currentLine = '';
      
      words.forEach(word => {
        const testLine = currentLine + (currentLine ? ' ' : '') + word;
        const metrics = ctx.measureText(testLine);
        if (metrics.width > maxWidth && currentLine !== '') {
          lines.push(currentLine);
          currentLine = word;
        } else {
          currentLine = testLine;
        }
      });
      if (currentLine) {
        lines.push(currentLine);
      }

      // Draw text background and text
      const totalHeight = lines.length * lineHeight;
      const startY = y1 + (height - totalHeight) / 2;

      lines.forEach((line, i) => {
        const textWidth = ctx.measureText(line).width;
        const textX = x1 + (width - textWidth) / 2;
        const textY = startY + i * lineHeight;

        // Draw background
        ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
        ctx.fillRect(textX - 2, textY - 2, textWidth + 4, fontSize + 4);

        // Draw text
        ctx.fillStyle = '#ffffff';
        ctx.fillText(line, textX, textY);
      });
    }
  });

  return timings;
};

class Colors {
  // ultralytics color palette https://ultralytics.com/
  constructor() {
    this.palette = [
      "#FF3838",
      "#FF9D97",
      "#FF701F",
      "#FFB21D",
      "#CFD231",
      "#48F90A",
      "#92CC17",
      "#3DDB86",
      "#1A9334",
      "#00D4BB",
      "#2C99A8",
      "#00C2FF",
      "#344593",
      "#6473FF",
      "#0018EC",
      "#8438FF",
      "#520085",
      "#CB38FF",
      "#FF95C8",
      "#FF37C7",
    ];
    this.n = this.palette.length;
  }

  get = (i) => this.palette[Math.floor(i) % this.n];

  static hexToRgba = (hex, alpha) => {
    var result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result
      ? `rgba(${[
          parseInt(result[1], 16),
          parseInt(result[2], 16),
          parseInt(result[3], 16),
        ].join(", ")}, ${alpha})`
      : null;
  };
}
