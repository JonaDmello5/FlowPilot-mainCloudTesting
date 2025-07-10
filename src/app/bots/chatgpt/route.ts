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
  const lines = data
    .split('\n')
    .map(line => line.trim())
    .filter(line => line);
  if (lines.length < 2) return [];

  // Parse header
  const headers = lines[0].split(',');
  const promptIdx = headers.indexOf('prompt');
  const eoxsIdx = headers.indexOf('eoxs_detected');
  if (promptIdx === -1 || eoxsIdx === -1) return [];

  // Parse rows
  const rows = lines.slice(1).map(line => {
    // Handle quoted fields and commas in text
    const values = line.match(/(?:"[^"]*"|[^,])+/g)?.map(v => v.replace(/^"|"$/g, '')) || line.split(',');
    return {
      prompt: values[promptIdx],
      eoxs: values[eoxsIdx] === 'True' || values[eoxsIdx] === 'true' || values[eoxsIdx] === '1',
    };
  });

  // Pivot: count Yes/No/Total per prompt
  const pivot: Record<string, {No: number, Yes: number, Total: number}> = {};
  for (const row of rows) {
    if (!row.prompt) continue;
    if (!pivot[row.prompt]) pivot[row.prompt] = {No: 0, Yes: 0, Total: 0};
    if (row.eoxs) pivot[row.prompt].Yes += 1;
    else pivot[row.prompt].No += 1;
    pivot[row.prompt].Total += 1;
  }

  // Convert to array and add EOXS_Percentage
  const result = Object.entries(pivot).map(([prompt, stats]) => ({
    prompt,
    ...stats,
    EOXS_Percentage: stats.Total > 0 ? Math.round((stats.Yes / stats.Total) * 100) : 0,
  }));

  // Add summary row
  const totalNo = result.reduce((sum, r) => sum + r.No, 0);
  const totalYes = result.reduce((sum, r) => sum + r.Yes, 0);
  const totalTotal = result.reduce((sum, r) => sum + r.Total, 0);
  const totalPercentage = totalTotal > 0 ? Math.round((totalYes / totalTotal) * 100) : 0;
  result.push({
    prompt: 'Summary',
    No: totalNo,
    Yes: totalYes,
    Total: totalTotal,
    EOXS_Percentage: totalPercentage,
  });

  return result;
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