// @ts-expect-error: Node.js built-in module used in API route
import { exec } from "child_process";

/**
 * Stops the pm2 process chatgpt-bot.
 * – If the bot is already stopped (or doesn't exist), still respond 200.
 * – On real failure respond 500 with JSON error.
 */
export async function POST() {
  return new Promise<Response>((resolve) => {
    exec("pm2 stop chatgpt-bot", (err: Error | null, stdout: string, stderr: string) => {
      const okExit = !err;
      const alreadyStopped =
        /process or namespace not found|online processes: 0|no process found/i.test(
          stdout + stderr
        );

      if (okExit || alreadyStopped) {
        resolve(
          new Response(JSON.stringify({ ok: true }), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          })
        );
      } else {
        console.error("pm2 stop error:", stderr);
        resolve(
          new Response(
            JSON.stringify({
              ok: false,
              error: stderr.trim() || "pm2 stop failed",
            }),
            { status: 500, headers: { "Content-Type": "application/json" } }
          )
        );
      }
    });
  });
} 