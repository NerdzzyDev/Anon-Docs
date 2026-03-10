const path = require("path");
const { app, BrowserWindow, shell } = require("electron");

const isDev = Boolean(process.env.ELECTRON_DEV_SERVER);

function createWindow() {
  const win = new BrowserWindow({
    width: 1280,
    height: 780,
    minWidth: 1100,
    minHeight: 680,
    backgroundColor: "#eef2f8",
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  if (isDev) {
    win.loadURL(process.env.ELECTRON_DEV_SERVER);
    win.webContents.openDevTools({ mode: "detach" });
  } else {
    const indexPath = path.join(process.resourcesPath, "frontend_dist", "index.html");
    win.loadFile(indexPath);
  }

  win.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: "deny" };
  });
}

app.whenReady().then(() => {
  createWindow();
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});
