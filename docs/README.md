YADT Spec
===

## YADT Document Processing Markup Language

dpml.v1.rng: The definition of the markup language acting as a intermidate representation between the parse and the render.

### An Example

```xml
<?xml version="1.0" encoding="UTF-8"?>
<wp:document xmlns:wp="urn:ns:yadt:dpml">
    <wp:page>
        <wp:page-properties>
            <wp:page-margins 
                top="2.54cm"
                bottom="2.54cm" 
                left="3.18cm"
                right="3.18cm"/>
            <wp:page-size 
                width="21cm"
                height="29.7cm"
                orient="portrait"
                code="A4"/>
        </wp:page-properties>
        
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

### Quick Reference

#### Document Structure
- `<wp:document>` - Root element
  - `<wp:page>` - Page container
    - `<wp:page-properties>` - Page configuration
      - `<wp:page-margins>` - Page margins (top, bottom, left, right)
      - `<wp:page-size>` - Page dimensions and orientation
    - `<wp:block>` - Content block container
      - Attributes: `offsetX`, `offsetY`, `width`, `height` (all accept auto/percentage/units)

#### Text Elements
- `<wp:p>` - Paragraph
  - Attributes: `align` (justify|center|right|start)
  - `<wp:run>` - Text run with styling
    - Attributes: `color`, `font-family`, `background-color`
    - Can contain: text, `<wp:break>`, `<wp:symbol>`, `<wp:math>`
  - `<wp:break>` - Line/page break
    - Attributes: `type` (line|column)
  - `<wp:math>` - Math expression (MathJax)
  - `<wp:symbol>` - Special character/symbol
    - Attributes: `src` (path to svg/png)

#### Tables
- `<wp:table>` - Table container
  - Attributes: `frame`, `width`, `rowsep`, `colsep`, `framestyle*`
  - `<wp:cols>` - Column definitions
    - `<wp:col>` - Single column
      - Attributes: `colwidth`
  - `<wp:thead>` - Table header
  - `<wp:tbody>` - Table body
    - `<wp:tr>` - Table row
      - `<wp:td>` - Table cell
        - Attributes: `align`, `colspan`, `rowspan`, `borderstyle*`, `bordercolor*`, `shade`

#### Objects
- `<wp:object>` - Special content container
  - `<wp:figure>` - Image/figure
    - Attributes: `src`, `width`, `height`, `caption`, `title`
  - `<wp:codeblock>` - Code block
    - Attributes: `language`
    - `<wp:codeline>` - Code line
      - Attributes: `number`, `highlight`

#### Common Attributes
- Measurements: Accept `auto`, percentages (e.g. "50%"), or units (pt|pc|mm|cm|in|em|px)
- Colors: 6-digit hex RGB (e.g. "FF0000" for red)
- Border styles: `single|double|dotted|dashed|none`

#### Example Usage
See the example above for practical implementation of these elements.

### Example Page Configuration

```xml
<?xml version="1.0" encoding="UTF-8"?>
<wp:document xmlns:wp="urn:ns:yadt:dpml">
    <wp:page>
        <wp:page-properties>
            <wp:page-margins 
                top="2.54cm"
                bottom="2.54cm" 
                left="3.18cm"
                right="3.18cm"/>
            <wp:page-size 
                width="21cm"
                height="29.7cm"
                orient="portrait"
                code="A4"/>
        </wp:page-properties>
        
        <!-- Content blocks go here -->
        <wp:block offsetX="10%" offsetY="5%" width="80%" height="auto">
            <!-- Block content -->
        </wp:block>
    </wp:page>
</wp:document>
```



