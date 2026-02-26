const xlsx = require('xlsx');

async function readExcel() {
    try {
        console.log("--- READING XLSX (Services Sheet.xlsx) ---");
        const workbook = xlsx.readFile('C:/Users/Admin/Bali Project/Services Sheet.xlsx');
        console.log("Sheet Names:", workbook.SheetNames);

        const sheetsToRead = ["Menu Structure", "QR codes", "Menu Design", "AI Data", "Platform Design"];
        for (const sheetName of sheetsToRead) {
            if (workbook.SheetNames.includes(sheetName)) {
                console.log(`\n\n--- SHEET: ${sheetName} ---`);
                const sheet = workbook.Sheets[sheetName];
                const data = xlsx.utils.sheet_to_json(sheet, { header: 1 });
                data.slice(0, 30).forEach(row => console.log(row.join(' | ')));
            } else {
                console.log(`\n\n--- SHEET ${sheetName} NOT FOUND ---`);
            }
        }
    } catch (error) {
        console.error("Error reading docs:", error);
    }
}

readExcel();
