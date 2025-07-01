import * as path from 'path';
import { Workbook } from 'exceljs';
import { promises as fs } from 'fs';

async function loadRows() {
  const csvPath = path.join(
    process.cwd(),
    'src',
    'app',
    'bots',
    'chatgpt',
    'logs',
    'logs.csv'
  );

  const data = await fs.readFile(csvPath, 'utf-8');
  const rows = data
    .split('\n')
    .map(line => line.trim())
    .filter(line => line)
    .map((line, index) => {
      if (index === 0) return null; // Skip header

      // Use regex to extract fields properly, including quoted strings
      const match = line.match(/^"?(.+?)"?,(\d+),(\d+),(\d+),/);
      if (!match) return null;

      const [, prompt, no, yes, total] = match;
      const noVal = parseInt(no);
      const yesVal = parseInt(yes);
      const totalVal = parseInt(total);
      const percentage = totalVal > 0 ? Math.round((yesVal / totalVal) * 100) : 0;

      return {
        prompt: prompt,
        No: noVal,
        Yes: yesVal,
        Total: totalVal,
        EOXS_Percentage: percentage,
      };
    })
    .filter(row => row !== null);

  // Calculate totals
  const totalNo = rows.reduce((sum, r) => sum + r.No, 0);
  const totalYes = rows.reduce((sum, r) => sum + r.Yes, 0);
  const totalTotal = rows.reduce((sum, r) => sum + r.Total, 0);
  const totalPercentage = totalTotal > 0 ? Math.round((totalYes / totalTotal) * 100) : 0;

  // Add summary row
  rows.push({
    prompt: 'Summary',
    No: totalNo,
    Yes: totalYes,
    Total: totalTotal,
    EOXS_Percentage: totalPercentage,
  });

  return rows;
}

export async function GET() {
  const data = await loadRows();

  const outWb = new Workbook();
  const outWs = outWb.addWorksheet('Pivot Summary');

  outWs.addRow(['prompt', 'No', 'Yes', 'Total', 'EOXS_Percentage']);

  data.forEach((r) => {
    outWs.addRow([r.prompt, r.No, r.Yes, r.Total, r.EOXS_Percentage]);
  });

  // Auto-width columns
  outWs.columns.forEach((col) => {
    let max = 10;
    col.eachCell({ includeEmpty: true }, (cell) => {
      const len = String(cell.value ?? '').length;
      if (len > max) max = len;
    });
    col.width = max + 2;
  });

  const buffer = await outWb.xlsx.writeBuffer();

  return new Response(buffer, {
    status: 200,
    headers: {
      'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'Content-Disposition': 'attachment; filename="chatgpt_pivot.xlsx"',
    },
  });
}