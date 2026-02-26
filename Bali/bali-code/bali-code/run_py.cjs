const { exec } = require('child_process');
const path = `"c:\\Users\\Admin\\Bali Project\\Bali\\bali-code\\bali-code\\easybali-backend\\.venv\\Scripts\\python.exe"`;
exec(path + ' test_lang.py', { cwd: 'c:/Users/Admin/Bali Project/Bali/bali-code/bali-code/easybali-backend' }, (error, stdout, stderr) => {
    if (error) {
        console.error(`exec error: ${error}`);
        return;
    }
    console.log(`stdout: ${stdout}`);
    console.error(`stderr: ${stderr}`);
});
