const fs = require('fs');

const filesToUpdate = [
    'src/page/dashboard/PassportVerification.jsx',
    'src/page/dashboard/Login.jsx',
    'src/page/dashboard/GuestActivity.jsx',
    'src/page/dashboard/DashboardMain.jsx',
    'src/page/dashboard/DashboardChats.jsx',
    'src/components/services/serviceItems.jsx',
    'src/components/services/api.jsx',
    'src/api/chatApi.jsx'
];

filesToUpdate.forEach(file => {
    try {
        let content = fs.readFileSync(file, 'utf8');

        const oldCode = `const API_BASE_URL = window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : 'https://bali-v92r.onrender.com';`;

        const newCode = `const API_BASE_URL = import.meta.env.VITE_API_URL || (window.location.hostname === 'localhost' ? 'http://localhost:8000' : 'https://bali-v92r.onrender.com');`;

        if (content.includes(oldCode)) {
            content = content.replace(oldCode, newCode);
            fs.writeFileSync(file, content);
            console.log(`Updated ${file} (ternary format)`);
        } else {
            let changed = false;

            const singleLineOld = "const API_BASE_URL = window.location.hostname === 'localhost' ? 'http://localhost:8000' : 'https://bali-v92r.onrender.com';";
            if (content.includes(singleLineOld)) {
                content = content.replace(singleLineOld, newCode);
                changed = true;
            }

            const rend = "'https://bali-v92r.onrender.com'";
            const rendDouble = '"https://bali-v92r.onrender.com"';
            const newRend = "(import.meta.env.VITE_API_URL || 'https://bali-v92r.onrender.com')";

            if (content.includes(rend)) {
                content = content.replaceAll(rend, newRend);
                changed = true;
            }
            if (content.includes(rendDouble)) {
                content = content.replaceAll(rendDouble, newRend);
                changed = true;
            }

            if (changed) {
                fs.writeFileSync(file, content);
                console.log(`Updated ${file} (inline format)`);
            } else {
                console.log(`No matching patterns found in ${file}`);
            }
        }
    } catch (e) {
        console.log(`Error reading ${file}: ${e.message}`);
    }
});
