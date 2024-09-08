let currentEmail = '';

document.getElementById('generateEmail').addEventListener('click', generateEmail);
document.getElementById('generateAnother').addEventListener('click', generateEmail);
document.getElementById('checkMail').addEventListener('click', checkMail);
document.getElementById('copyButton').addEventListener('click', copyEmail);

// Load the last used email from localStorage
window.onload = function() {
    const savedEmail = localStorage.getItem('lastEmail');
    if (savedEmail) {
        currentEmail = savedEmail;
        document.getElementById('emailDisplay').innerText = currentEmail;
        document.getElementById('generateEmail').style.display = 'none';
        document.getElementById('generateAnother').style.display = 'inline';
        document.getElementById('copyButton').style.display = 'inline';
        document.getElementById('inbox').style.display = 'block';
    }
};

function generateEmail() {
    fetch('https://www.1secmail.com/api/v1/?action=getDomainList')
        .then(response => response.json())
        .then(domains => {
            const username = Math.random().toString(36).substring(2, 10);
            const domain = domains[Math.floor(Math.random() * domains.length)];
            currentEmail = `${username}@${domain}`;
            document.getElementById('emailDisplay').innerText = currentEmail;
            document.getElementById('generateEmail').style.display = 'none';
            document.getElementById('generateAnother').style.display = 'inline';
            document.getElementById('copyButton').style.display = 'inline';
            document.getElementById('inbox').style.display = 'block';
            localStorage.setItem('lastEmail', currentEmail); // Save the email to localStorage
        });
}

function copyEmail() {
    const emailText = document.getElementById('emailDisplay').innerText;
    navigator.clipboard.writeText(emailText);
}

function checkMail() {
    const [username, domain] = currentEmail.split('@');
    fetch(`https://www.1secmail.com/api/v1/?action=getMessages&login=${username}&domain=${domain}`)
        .then(response => response.json())
        .then(data => {
            if (data.length > 0) {
                const messageId = data[0].id;
                fetch(`https://www.1secmail.com/api/v1/?action=readMessage&login=${username}&domain=${domain}&id=${messageId}`)
                    .then(response => response.json())
                    .then(message => {
                        document.getElementById('mailContent').innerHTML = `
                            <p>Subject: ${message.subject}</p>
                            <p>From: ${message.from}</p>
                            <p>Date: ${message.date}</p>
                            <p>Body: ${message.body}</p>
                        `;
                    });
            } else {
                document.getElementById('mailContent').innerText = 'No new messages.';
 
           }
        });
}
