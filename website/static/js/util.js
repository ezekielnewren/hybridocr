function assert(condition, message) {
    if (!condition) {
        throw new Error(message || 'Assertion failed');
    }
}


function escapeHtml(unsafe) {
    // https://stackoverflow.com/a/6234804
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

async function register(_id, email) {
    if (_id == null && email == null) {
        throw new Error("must supply _id or email");
    }

    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    let require_email = _id == null;
    if ((require_email || email != null) && !emailPattern.test(email)) {
        throw new Error("Invalid email address");
    }

    let data = {};
    if (_id != null) {
        data["_id"] = _id;
    }
    if (email != null) {
        data["email"] = email;
    }

    const response = await fetch('/register', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    });

    if (response.ok) {
        return {success: true}
    } else {
        return {errors: [`Failed to submit email: ${response.status} ${response.statusText}`]};
    }
}
