const fs = require('fs');
const files = [
    'bali-frontend/src/api/chatApi.jsx',
    'bali-frontend/src/components/services/api.jsx',
    'bali-frontend/src/page/dashboard/DashboardChats.jsx',
    'bali-frontend/src/page/dashboard/DashboardMain.jsx',
    'bali-frontend/src/page/dashboard/GuestActivity.jsx',
    'bali-frontend/src/page/dashboard/Login.jsx'
];

files.forEach(f => {
    let path = 'c:/Users/Admin/Bali Project/Bali/bali-code/bali-code/' + f;
    let c = fs.readFileSync(path, 'utf8');
    let newC = c.replace(/import\.meta\.env\.VITE_BASE_URL \|\| 'https:\/\/easy-bali\.onrender\.com'/g, "'https://easy-bali.onrender.com'");
    if (c !== newC) {
        fs.writeFileSync(path, newC);
        console.log('Fixed ' + path);
    } else {
        console.log('No change in ' + path);
    }
});
