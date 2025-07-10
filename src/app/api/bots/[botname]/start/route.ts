// src/app/api/bots/[botName]/start/route.ts

// If you see type errors for Node.js modules, ensure you have @types/node installed:
// npm i --save-dev @types/node
import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';
import { spawn, ChildProcess } from 'child_process';
import path from 'path';
import fs from 'fs';
import { Buffer } from 'buffer'; // Add this for Buffer type

export async function POST(
  req: NextRequest,
  context: { params: Promise<{ botName: string }> }
) {
  const { botName } = await context.params; 
  console.log('🐛 [start] params.botName =', JSON.stringify(botName));

  // Validate bot name
  if (!botName || !['chatgpt', 'perplexity'].includes(botName)) {
    return NextResponse.json(
      { error: 'Invalid bot name. Must be "chatgpt" or "perplexity"', received: botName },
      { status: 400 }
    );
  }

  try {
    // Base folder for this bot
    const scriptDir = path.join(
      process.cwd(),
      'src',
      'app',
      'bots',
      botName
    );

    // Path to the Python entrypoint
    const scriptPath = path.join(scriptDir, 'main.py');

    // Check that main.py actually exists
    if (!fs.existsSync(scriptPath)) {
      return NextResponse.json(
        { error: `Bot script not found: ${scriptPath}` },
        { status: 404 }
      );
    }

    // Spawn the bot process
    // Use '-u' for unbuffered output so logs appear immediately in pm2 logs
    const pythonProcess: ChildProcess = spawn('python3', ['-u', scriptPath], {
      stdio: 'pipe',
      shell: true,
    });

    // Write its PID into a file alongside the script
    const pidFile = path.join(scriptDir, `${botName}.pid`);
    fs.writeFileSync(pidFile, String(pythonProcess.pid), 'utf-8');

    // Helper to prefix logs with timestamp
    function logWithTimestamp(prefix: string, msg: string) {
      const now = new Date().toISOString();
      console.log(`[${now}] [Bot: ${botName}] ${prefix}: ${msg}`);
    }

    // Log output for debugging, with timestamp
    pythonProcess.stdout?.on('data', (data: Buffer) => {
      logWithTimestamp('stdout', data.toString().trim());
    });
    pythonProcess.stderr?.on('data', (data: Buffer) => {
      logWithTimestamp('stderr', data.toString().trim());
    });
    pythonProcess.on('close', (code: number) => {
      logWithTimestamp('exit', `process exited with code ${code}`);
      // Clean up the PID file when the process ends
      if (fs.existsSync(pidFile)) fs.unlinkSync(pidFile);
    });

    return NextResponse.json({
      status: 'started',
      bot: botName,
    });
  } catch (error: any) {
    console.error(`Error starting bot "${botName}":`, error);
    return NextResponse.json(
      { error: 'Failed to start bot', details: (error as Error).message },
      { status: 500 }
    );
  }
}
