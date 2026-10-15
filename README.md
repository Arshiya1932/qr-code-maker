# qr-code-maker
🎨 Pro QR Code scanner

Hey there! I got tired of paying subscriptions for QR code generators just to put a simple logo in the middle of a code. So, I decided to build my own. 

This is a fully-featured desktop app that lets you generate crazy stylized QR codes, drop in GIFs, add custom frames, and even batch-generate hundreds of codes at once. No internet connection required (unless you want to use the link shortener!).
✨ What can it do?

    Drop in Logos or GIFs: Put an image or animated GIF right in the center. It automatically adds a white background behind it so the code still scans perfectly.
    Custom Shapes & Colors: Make the QR pixels rounded, circular, or standard. Change the colors, or even apply a vertical gradient.
    Call-to-Action Frames: Automatically wrap your code in a border that says "SCAN ME", "SCAN TO PAY", or whatever custom text you want.
    Export Anywhere: Save as a high-res PNG, an animated GIF, an infinitely scalable SVG vector, or a print-ready A4 PDF (complete with crop marks!).
    Batch Generator: Got a spreadsheet of 500 links? Upload the CSV, pick a logo, and it spits out a ZIP file of 500 branded QR codes in seconds.
    Built-in Scanner: Need to read a QR code? Just load an image file into the app and it'll decode it for you.
    Sleek Dark Mode: Because staring at bright white windows at 2 AM sucks.
    Drag & Drop: Just drag an image from your desktop straight onto the app window.

🚀 Getting Started

Getting this running on your machine is super easy. 

1. Install the dependencies:Just run this single command in your terminal/command prompt:

pip install qrcode[pil] Pillow tkinterdnd2 opencv-python numpy
paste this in terminal/cmd

2. Run the app
 
 
That's it! The app will create an arshiya folder in the same directory where it automatically saves all your generated QR codes by default.
🛠️ Built With

     Python & Tkinter (for the UI)
     Pillow (for all the heavy image editing and masking)
     qrcode (for the actual QR matrix generation)
     OpenCV (for the image scanner)
