const xlsx = require('xlsx');
const workbook = xlsx.readFile('Services Sheet.xlsx');
console.log('Sheet Names:', workbook.SheetNames);
workbook.SheetNames.forEach(name => {
    const sheet = workbook.Sheets[name];
    const range = xlsx.utils.decode_range(sheet['!ref']);
    console.log(`Sheet: ${name}, Rows: ${range.e.r + 1}, Cols: ${range.e.c + 1}`);
    const data = xlsx.utils.sheet_to_json(sheet, { header: 1 });
    if (data.length > 0) {
        console.log('Sample Headers:', data[0]);
    }
});
