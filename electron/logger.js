const fs = require('fs');
const path = require('path');

const MAX_SIZE = 2 * 1024 * 1024;
const MAX_FILES = 3;

// Fichier de log avec rotation : app.log, app.log.1, app.log.2
function createLogger(logDir, fileName = 'app.log') {
  const logPath = path.join(logDir, fileName);
  let enabled = true;

  try {
    fs.mkdirSync(logDir, { recursive: true });
  } catch {
    enabled = false;
  }

  function rotate() {
    for (let i = MAX_FILES - 1; i >= 1; i--) {
      const from = i === 1 ? logPath : `${logPath}.${i - 1}`;
      const to = `${logPath}.${i}`;
      if (fs.existsSync(from)) {
        fs.renameSync(from, to);
      }
    }
  }

  function write(message) {
    if (!enabled) return;
    try {
      if (fs.existsSync(logPath) && fs.statSync(logPath).size >= MAX_SIZE) {
        rotate();
      }
      fs.appendFileSync(logPath, `${new Date().toISOString()} ${message}\n`);
    } catch {
      // Un probleme de log ne doit jamais faire planter l'application
      enabled = false;
    }
  }

  return { write, logPath };
}

module.exports = { createLogger };
