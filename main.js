const { app, BrowserWindow, nativeTheme } = require('electron')

// janela principal
const createWindow = () => {
    nativeTheme.themeSource = 'dark'
    const win = new BrowserWindow({
        width: 1600,
        height: 900,
        icon: './src/public/img/favicon-_1_.png',
        /*resizable: false //impede de ser redimerencionada*/
        autoHideMenuBar: true,
        /*titleBarStyle: 'hidden'*/
    })

    // CORREÇÃO: Certifique-se de que o caminho 'scr' está correto. 
    // Assumi que você quis dizer 'src' (source).
    win.loadFile('./src/views/index.html') 
}

// janela consulta
const aboutWindow = () => {
    // A variável que armazena a nova janela é 'aboutWindow'
    const newAboutWindow = new BrowserWindow({ // Renomeei para 'newAboutWindow' para evitar confusão de nomes
        width: 1600,
        height: 900,
        icon: './src/public/img/favicon-_1_.png',
        autoHideMenuBar: true
    })

    // CORREÇÃO ESSENCIAL: 
    // 1. Usando a variável correta: 'newAboutWindow'
    // 2. Usando o método correto: '.loadFile' (com 'L' maiúsculo)
    newAboutWindow.loadFile('./src/views/consulta.html') 
}

// Inicializa a aplicação
app.whenReady().then(() => {
    createWindow()
    //aboutWindow()

    // Este listener garante que, se todas as janelas forem fechadas e 
    // a aplicação estiver ativa (como no macOS), uma nova janela seja criada.
    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) createWindow()
    })
})

// Fecha a aplicação quando todas as janelas estiverem fechadas (exceto no macOS)
app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') app.quit()
})