document.addEventListener('DOMContentLoaded', () => {
    const contactForm = document.getElementById('contactForm');
    const statusMessage = document.getElementById('statusMessage');
    const submitBtn = document.getElementById('submitBtn');

    contactForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Disable submit button and show loading state
        submitBtn.disabled = true;
        submitBtn.textContent = 'Submitting...';
        statusMessage.textContent = '';
        statusMessage.className = '';
        
        try {
            const formData = new FormData(contactForm);
            
            // First, check if there's a resume file to upload
            const resumeFile = formData.get('resume');
            let resumeUrl = '';
            
            if (resumeFile && resumeFile.size > 0) {
                // Get pre-signed URL for S3 upload
                const presignedUrlResponse = await fetch('/api/get-upload-url', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        fileName: resumeFile.name,
                        fileType: resumeFile.type
                    })
                });
                
                if (!presignedUrlResponse.ok) {
                    throw new Error('Failed to get upload URL');
                }
                
                const { uploadUrl, fileUrl } = await presignedUrlResponse.json();
                
                // Upload file directly to S3 using pre-signed URL
                const uploadResponse = await fetch(uploadUrl, {
                    method: 'PUT',
                    body: resumeFile,
                    headers: {
                        'Content-Type': resumeFile.type
                    }
                });
                
                if (!uploadResponse.ok) {
                    throw new Error('Failed to upload resume');
                }
                
                resumeUrl = fileUrl;
            }
            
            // Create contact data object
            const contactData = {
                firstName: formData.get('firstName'),
                lastName: formData.get('lastName'),
                phoneNumber: formData.get('phoneNumber') || null,
                email: formData.get('email'),
                resumeUrl: resumeUrl || null
            };
            
            // Submit contact data to API
            const response = await fetch('/api/submit-contact', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(contactData)
            });
            
            if (!response.ok) {
                throw new Error('Failed to submit contact information');
            }
            
            // Show success message
            statusMessage.textContent = 'Contact information submitted successfully!';
            statusMessage.className = 'success';
            contactForm.reset();
            
        } catch (error) {
            console.error('Error:', error);
            statusMessage.textContent = error.message || 'An error occurred. Please try again.';
            statusMessage.className = 'error';
        } finally {
            // Re-enable submit button
            submitBtn.disabled = false;
            submitBtn.textContent = 'Submit';
        }
    });
});