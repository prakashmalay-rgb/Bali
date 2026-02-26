const fs = require('fs');
const xlsx = require('xlsx');
const pdf = require('pdf-parse');
const mammoth = require('mammoth');

async function readDocs() {
    try {
        console.log("--- READING XLSX (Services Sheet.xlsx) ---");
        const workbook = xlsx.readFile('C:/Users/Admin/Bali Project/Services Sheet.xlsx');
        console.log("Sheet Names:", workbook.SheetNames);

        for (const sheetName of workbook.SheetNames) {
            console.log(`\n\n--- SHEET: ${sheetName} ---`);
            const sheet = workbook.Sheets[sheetName];
            const data = xlsx.utils.sheet_to_json(sheet, { header: 1 });
            // Print only first few rows
            data.slice(0, 50).forEach(row => console.log(row.join(' | ')));
        }

        console.log("\n\n--- READING PDF (EASY Bali x Prakash Malayalam.pdf) ---");
        const dataBuffer = fs.readFileSync('C:/Users/Admin/Bali Project/EASY Bali x Prakash Malayalam.pdf');
        const pdfData = await pdf(dataBuffer);
        console.log(pdfData.text.substring(0, 3000));

        console.log("\n\n--- READING DOCX (🌴 EASY Bali – Dev Brief For Incoming Developer.docx) ---");
        const docxResult = await mammoth.extractRawText({ path: "C:/Users/Admin/Bali Project/🌴 EASY Bali – Dev Brief For Incoming Developer.docx" });
        console.log(docxResult.value.substring(0, 3000));

    } catch (error) {
        console.error("Error reading docs:", error);
    }
}

readDocs();
