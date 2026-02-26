const fs = require('fs');
const pdf = require('pdf-parse');
const mammoth = require('mammoth');

async function readDocs() {
    try {
        console.log("--- READING PDF (EASY Bali x Prakash Malayalam.pdf) ---");
        const dataBuffer = fs.readFileSync('C:/Users/Admin/Bali Project/EASY Bali x Prakash Malayalam.pdf');
        try {
            const pdfData = await pdf(dataBuffer);
            console.log(pdfData.text.substring(0, 5000));
        } catch (e) {
            console.error("PDF Parse error", e);
        }

        console.log("\n\n--- READING DOCX (🌴 EASY Bali – Dev Brief For Incoming Developer.docx) ---");
        try {
            const docxResult = await mammoth.extractRawText({ path: "C:/Users/Admin/Bali Project/🌴 EASY Bali – Dev Brief For Incoming Developer.docx" });
            console.log(docxResult.value.substring(0, 5000));
        } catch (e) {
            console.error("DOCX error", e);
        }

    } catch (error) {
        console.error("Error reading docs:", error);
    }
}

readDocs();
