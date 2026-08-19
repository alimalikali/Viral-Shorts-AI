const { app, BrowserWindow } = require('electron');
const path = require('path');

function createWindow() {
  const mainWindow = new BrowserWindow({
    width: 1440,
    height: 960,
    minWidth: 1024,
    minHeight: 768,
    title: "Viral Shorts AI - Desktop Editor",
    backgroundColor: "#09090b", // Deep onyx color matching index.html
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true
    }
  });

  // Load local React Vite dev server
  // When deploying for production, this will point to compiled build folders
  mainWindow.loadURL(`http://localhost:${process.env.FRONTEND_PORT || 3000}`);

  // Remove native frame menu bars for clean CapCut look
  mainWindow.setMenuBarVisibility(false);
}

app.whenReady().then(() => {
  createWindow();

  app.on('activate', function () {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') app.quit();
});
