function downloadCertificate() {
    const buttons = document.querySelector('.no-print');

    // Hide buttons before capture
    buttons.style.display = 'none';

    const printArea = document.querySelector('.cert-container');

    html2canvas(printArea, { 
        scale: 2,
        useCORS: true
    }).then(canvas => {
        const imgData = canvas.toDataURL('image/png');
        const { jsPDF } = window.jspdf;
        const pdf = new jsPDF('p', 'mm', 'a4');

        const imgWidth = 210;
        const imgHeight = (canvas.height * imgWidth) / canvas.width;

        pdf.addImage(imgData, 'PNG', 0, 0, imgWidth, imgHeight);

        pdf.save(`quizo-certificate.pdf`);

        // Show buttons again after capture
        buttons.style.display = 'block';
    });
}