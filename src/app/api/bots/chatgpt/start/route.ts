import { exec } from "child_process";

/**
 * Starts the pm2 process chatgpt-bot.
 * – If the bot is already online, still respond 200.
 * – On real failure respond 500 with stderr text.
 */
export async function POST() {
  return new Promise<Response>((resolve) => {
    exec("pm2 start chatgpt-bot", (err, stdout, stderr) => {
      const okExit = !err;
      const alreadyRunning =
        /already\s+online|name\s+.*exist|Process\s+successfully\s+started/i.test(
          stdout + stderr
        );

      if (okExit || alreadyRunning) {
        resolve(new Response("chatgpt-bot running", { status: 200 }));
      } else {
        console.error("pm2 start error:", stderr);
        resolve(new Response(stderr.trim() || "pm2 start failed", { status: 500 }));
      }
    });
  });
} 