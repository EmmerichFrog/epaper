document.addEventListener("DOMContentLoaded", () => {
    const uploadForm = document.getElementById("uploadForm");
    const fileInput = document.getElementById("fileInput");
    const uploadBtn = document.getElementById("uploadBtn");
    const progressContainer = document.getElementById("progressContainer");
    const progressBar = document.getElementById("progressBar");
    const imageContainer = document.getElementById("imageContainer");
    const headerImg = document.getElementById("headImg");
    const uploadedImage = document.getElementById("uploadedImage");
    const cropBtn = document.getElementById("cropBtn");
    const okBtn = document.getElementById("okBtn");
    const vertBtn = document.getElementById("vertBtn");
    const horBtn = document.getElementById("horBtn");

    let cropper;

    uploadBtn.addEventListener("click", () => {
        uploadedImage.style.width = " ";
        uploadedImage.style.marginLeft = " ";
        uploadedImage.style.marginRight = " ";
        const file = fileInput.files[0];
        if (!file) return alert("Please select a file!");

        const formData = new FormData();
        formData.append("file", file);

        const xhr = new XMLHttpRequest();
        xhr.open("POST", "/upload", true);

        xhr.upload.onprogress = (event) => {
            if (event.lengthComputable) {
                const percentComplete = Math.round((event.loaded / event.total) * 100);
                progressContainer.style.display = "block";
                progressBar.style.width = percentComplete + "%";
                progressBar.textContent = percentComplete + "%";
            }
        };

        xhr.onload = function () {
            if (cropper) { cropper.destroy() };
            const response = JSON.parse(xhr.responseText);
            const imageUrl = `/uploads/${response.filename}`;
            uploadedImage.src = imageUrl;
            headerImg.style.display = "none";
            imageContainer.style.display = "grid";
            okBtn.style.display = "block";
            cropBtn.style.display = "none";
            horBtn.style.display = "none";
            vertBtn.style.display = "none";
        };

        xhr.send(formData);

    });

    okBtn.addEventListener("click", () => {
        progressBar.style.display = "none"
        const aspectRatio = calculateAspectRatio(uploadedImage.naturalWidth, uploadedImage.naturalHeight);

        function calculateAspectRatio(width, height) {
            if (width > height) {
                return 5 / 3; // Landscape
            } else if (height > width) {
                return 3 / 5; // Portrait
            } else {
                return 1; // Square
            }
        }
        if (cropper) { cropper.destroy() };
        cropper = new Cropper(uploadedImage, {
            aspectRatio: aspectRatio,
            viewMode: 1,
            zoomable: false,
        });
        okBtn.style.display = "none";
        cropBtn.style.display = "block";
        vertBtn.style.display = "block";
        horBtn.style.display = "block";

    })

    vertBtn.addEventListener("click", () => {
        if (cropper) { cropper.destroy() };
        cropper = new Cropper(uploadedImage, {
            aspectRatio: 3 / 5,
            viewMode: 1,
            zoomable: false,
        });

    })

    horBtn.addEventListener("click", () => {
        if (cropper) { cropper.destroy() };
        cropper = new Cropper(uploadedImage, {
            aspectRatio: 5 / 3,
            viewMode: 1,
            zoomable: false,
        });

    })



    cropBtn.addEventListener("click", () => {
        const MAX_WIDTH = 800;
        const MAX_HEIGHT = 800;
        const croppedCanvas = cropper.getCroppedCanvas();
        cropper.destroy();
        if (croppedCanvas) {
            // Step 1: Scale the cropped canvas to the maximum size
            const resizedCanvas = resizeCanvas(croppedCanvas, MAX_WIDTH, MAX_HEIGHT);
            const croppedImage = resizedCanvas.toDataURL("image/jpeg", 0.7);
            uploadedImage.style.width = "75%";
            uploadedImage.style.marginLeft = " auto";
            uploadedImage.style.marginRight = " auto";
            uploadedImage.src = croppedImage;
            okBtn.style.display = "none";
            cropBtn.style.display = "none";
            horBtn.style.display = "none";
            vertBtn.style.display = "none";
            const formData = new FormData();

            formData.append("cropped_image_data", croppedImage);

            const xhr = new XMLHttpRequest();
            xhr.open("POST", `/converted`, true);

            xhr.send(formData);
        }


        // Function to resize the canvas while maintaining aspect ratio
        function resizeCanvas(canvas, maxWidth, maxHeight) {
            const width = canvas.width;
            const height = canvas.height;
            let newWidth = width;
            let newHeight = height;

            // Calculate the new dimensions while maintaining aspect ratio
            if (width > height && width > maxWidth) {
                newWidth = maxWidth;
                newHeight = (height * maxWidth) / width;
            } else if (height > width && height > maxHeight) {
                newHeight = maxHeight;
                newWidth = (width * maxHeight) / height;
            } else if (width > maxWidth) {
                newWidth = maxWidth;
                newHeight = (height * maxWidth) / width;
            } else if (height > maxHeight) {
                newHeight = maxHeight;
                newWidth = (width * maxHeight) / height;
            }
            // Create a new canvas to draw the resized image
            const resizedCanvas = document.createElement('canvas');
            resizedCanvas.width = newWidth;
            resizedCanvas.height = newHeight;

            const ctx = resizedCanvas.getContext('2d');
            ctx.drawImage(canvas, 0, 0, newWidth, newHeight);
            return resizedCanvas;
        };
    }
    );

});


