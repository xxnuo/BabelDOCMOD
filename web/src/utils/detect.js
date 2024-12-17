import { Tensor } from "onnxruntime-web";
import { renderBoxes } from "./renderBox";

/**
 * Transpose tensor
 * @param {Tensor} tensor Input tensor
 * @param {number[]} perm Transpose order, e.g. [1,0,2] means swapping the 0th and 1st dimensions
 * @returns {Tensor} Transposed new tensor
 */
function transposeTensor(tensor, perm) {
  const dims = tensor.dims;
  
  // If perm is not specified, reverse all dimensions by default
  if (!perm) {
    perm = dims.map((_, i) => dims.length - 1 - i);
  }
  
  // Calculate new dimensions
  const newDims = perm.map(i => dims[i]);
  
  // Create new data array
  const newData = new Float32Array(tensor.data.length);
  
  // Calculate strides for each dimension
  const strides = new Array(dims.length);
  strides[dims.length - 1] = 1;
  for (let i = dims.length - 2; i >= 0; i--) {
    strides[i] = strides[i + 1] * dims[i + 1];
  }
  
  // Calculate strides for transposed dimensions
  const newStrides = perm.map(i => strides[i]);
  
  // Traverse all elements for transposition
  for (let i = 0; i < tensor.data.length; i++) {
    // Calculate indices for original dimension values
    let temp = i;
    const indices = new Array(dims.length);
    for (let j = 0; j < dims.length; j++) {
      indices[j] = Math.floor(temp / strides[j]);
      temp %= strides[j];
    }
    
    // Calculate new index for transposed dimension
    let newIndex = 0;
    for (let j = 0; j < dims.length; j++) {
      newIndex += indices[perm[j]] * newStrides[j];
    }
    
    newData[newIndex] = tensor.data[i];
  }
  
  // Create new tensor
  return new Tensor(tensor.type, newData, newDims);
}

/**
 * Detect Image
 * @param {String} image Image URL
 * @param {HTMLCanvasElement} canvas canvas to draw boxes
 * @param {ort.InferenceSession} session YOLOv10 onnxruntime session
 * @param {Number} scoreThreshold Float representing the threshold for deciding when to remove boxes based on score
 * @param {Number[]} inputShape model input shape. Normally in YOLO model [batch, channels, width, height]
 * @param {HTMLElement} timeRef
 */
export const detectImage = async (
  image,
  canvas,
  session,
  scoreThreshold,
  inputShape,
  timeRef = null
) => {
  // clean up canvas
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);

  const imageT = await Tensor.fromImage(image, { tensorFormat: "RGB" });

  const [modelHeight, modelWidth] = inputShape.slice(2);
  const [imgHeight, imgWidth] = imageT.dims.slice(2);

  // Padding
  const max_ = Math.max(imgWidth, imgHeight);
  const padWidth = max_ - imgWidth;
  const padHeight = max_ - imgHeight;
  const padL = Math.floor(padWidth / 2);
  const padR = padWidth - padL;
  const padU = Math.floor(padHeight / 2);
  const padB = padHeight - padU;

  const padding = new Tensor(
    "int64",
    new BigInt64Array([padU, padL, padB, padR].map((e) => BigInt(e))) // [up, left, bottom, right]
  );

  // Resizing
  const scaleH = modelHeight / max_;
  const scaleW = modelWidth / max_;

  const scales = new Tensor(
    "float32",
    new Float32Array([scaleH, scaleW]) // [sh, sw]
  );

  const start = Date.now();
  const { letterbox } = await session.prep.run({
    images: imageT,
    padding: padding,
    scales: scales,
  }); // run preprocessing, padding and resize

  const { output0 } = await session.net.run({ images: letterbox }); // run session and get output layer
  const inferenceTime = Date.now() - start;
  
  const boxes = [];

  // const transposed = transposeTensor(output0, [0, 2, 1]);
  for (let idx = 0; idx < output0.dims[2]; idx++) {
    let x = output0.data[idx]  // 中心点x
    let y = output0.data[idx + output0.dims[2]]  // 中心点y 
    let w = output0.data[idx + output0.dims[2] * 2]  // 宽度
    let h = output0.data[idx + output0.dims[2] * 3]  // 高度
    let conf = output0.data[idx + output0.dims[2] * 4]  // 置信度

    if (conf < 0.45) continue; // 使用传入的scoreThreshold
    
    // 2. 还原到原始图像尺寸
    // 处理padding
    x = x / scaleW - padL
    y = y / scaleH - padU
    w = w / scaleW
    h = h / scaleH

    // 3. 从中心点+宽高格式转换为左上角+宽高格式
    const x1 = Math.round(x - w/2)
    const y1 = Math.round(y - h/2)
    const width = Math.round(w)
    const height = Math.round(h)

    boxes.push({
      label: 0,  // 如果只有一个类别就是0
      probability: conf,
      bounding: [x1, y1, width, height]
    });
  }

  // 添加计算IOU的辅助函数
  function calculateIOU(box1, box2) {
    // 转换为x1,y1,x2,y2格式
    const [x1, y1, w1, h1] = box1;
    const [x2, y2, w2, h2] = box2;
    
    const box1_x2 = x1 + w1;
    const box1_y2 = y1 + h1;
    const box2_x2 = x2 + w2;
    const box2_y2 = y2 + h2;

    // 计算交集区域
    const intersect_x1 = Math.max(x1, x2);
    const intersect_y1 = Math.max(y1, y2);
    const intersect_x2 = Math.min(box1_x2, box2_x2);
    const intersect_y2 = Math.min(box1_y2, box2_y2);

    // 无重叠区域
    if (intersect_x2 < intersect_x1 || intersect_y2 < intersect_y1) {
      return 0.0;
    }

    const intersect_area = (intersect_x2 - intersect_x1) * (intersect_y2 - intersect_y1);
    const box1_area = w1 * h1;
    const box2_area = w2 * h2;

    // 计算IOU
    return intersect_area / (box1_area + box2_area - intersect_area);
  }

  // 添加NMS函数
  function nms(boxes, iouThreshold = 0.45) {
    // 按置信度排序
    boxes.sort((a, b) => b.probability - a.probability);
    
    const selected = [];
    const len = boxes.length;
    const picked = new Array(len).fill(false);

    for (let i = 0; i < len; i++) {
      if (picked[i]) continue;
      
      selected.push(boxes[i]);
      picked[i] = true;

      // 与其他框计算IOU
      for (let j = i + 1; j < len; j++) {
        if (picked[j]) continue;
        
        const iou = calculateIOU(boxes[i].bounding, boxes[j].bounding);
        if (iou > iouThreshold) {
          picked[j] = true; // 抑制重叠框
        }
      }
    }

    return selected;
  }

  // 应用NMS
  const nmsBoxes = nms(boxes, 0.45); // 可以调整IOU阈值

  // rendering result
  // set canvas res the same as image res
  ctx.canvas.width = imgWidth;
  ctx.canvas.height = imgHeight;

  ctx.putImageData(await imageT.toImageData(), 0, 0); // Draw image
  const timings = await renderBoxes(ctx, nmsBoxes); // Draw boxes
  
  if (timeRef) {
    timeRef.innerText = `Model: ${normalizeTime(inferenceTime)}\nOCR: ${normalizeTime(timings.ocr)}\nTranslation: ${normalizeTime(timings.translation)}`;
  }
};

const normalizeTime = (time) => {
  if (time < 1000) return `${time} ms`;
  else if (time < 60000) return `${(time / 1000).toFixed(2)} S`;
  return `${(time / 60000).toFixed(2)} H`;
};
