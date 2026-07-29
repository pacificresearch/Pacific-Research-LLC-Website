// Render a resume JSON model (from tools/resume_render.py) to a plain .docx.
// Usage: node tools/resume_docx.js tailored/<name>.json
// Style rules: upright Calibri only, no italics, standard bullets, keepNext
// so job headers never orphan from their bullets.
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, AlignmentType, LevelFormat,
  BorderStyle, convertInchesToTwip,
} = require("docx");

const model = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const FONT = "Calibri";

const bind = (t) => t.replace(/ \| /g, "\u00a0| "); // bars end lines, never start them
const runSized = (text, bold, size) => new TextRun({ text: bind(text), font: FONT, size, bold: !!bold });
const run = (text, bold) => new TextRun({ text: bind(text), font: FONT, size: 21, bold: !!bold });

// "**Label:** rest" or "**Label** | rest" -> [bold, plain] runs
function boldRuns(text) {
  const m = text.match(/^\*\*(.+?)\*\*(.*)$/);
  if (m) return [run(m[1], true), run(m[2])];
  return [run(text)];
}

function nowrapDates(text) {
  // Date segment must never wrap leaving a lone year on the next line.
  const segs = text.split(" | ");
  const last = segs.length - 1;
  segs[last] = segs[last].replace(/ /g, "\u00a0").replace(/-/g, "\u2011");
  return segs.join(" | ");
}

function jobRuns(text) {
  text = nowrapDates(text);
  const i = text.indexOf(" | ");
  if (i === -1) return [runSized(text, true, 19)];
  return [runSized(text.slice(0, i), true, 19), runSized(text.slice(i), false, 19)];
}

const center = (text, size, bold, after) => new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { after },
  children: [new TextRun({ text: bind(text), font: FONT, size, bold })],
});

const sectionHeader = (text) => new Paragraph({
  spacing: { before: 200, after: 80 }, keepNext: true,
  border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "444444" } },
  children: [new TextRun({ text, font: FONT, size: 22, bold: true })],
});

const children = [
  center(model.name, 32, true, 60),
  center(model.contact, 19, false, 80),
  center(model.headline, 23, true, 120),
  new Paragraph({ spacing: { after: 60 }, children: [run(model.summary)] }),
];

for (const sec of model.sections) {
  children.push(sectionHeader(sec.title));
  for (const it of sec.items) {
    if (it.type === "job") {
      children.push(new Paragraph({
        spacing: { before: 140, after: 40 }, keepNext: true,
        children: jobRuns(it.text),
      }));
    } else if (it.type === "bullet") {
      const next = sec.items[sec.items.indexOf(it) + 1];
      children.push(new Paragraph({
        numbering: { reference: "resume-bullets", level: 0 },
        keepNext: !!(next && next.type === "bullet"),
        spacing: { after: 30 }, children: [run(it.text)],
      }));
    } else {
      children.push(new Paragraph({ spacing: { after: 40 }, children: boldRuns(it.text) }));
    }
  }
}

const doc = new Document({
  numbering: {
    config: [{
      reference: "resume-bullets",
      levels: [{
        level: 0, format: LevelFormat.BULLET, text: "•",
        alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: convertInchesToTwip(0.25), hanging: convertInchesToTwip(0.15) } } },
      }],
    }],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: {
          top: convertInchesToTwip(0.6), bottom: convertInchesToTwip(0.6),
          left: convertInchesToTwip(0.6), right: convertInchesToTwip(0.6),
        },
      },
    },
    children,
  }],
});

const out = process.argv[2].replace(/\.json$/, ".docx");
Packer.toBuffer(doc).then(buf => { fs.writeFileSync(out, buf); console.log("written:", out); });
