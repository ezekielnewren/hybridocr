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
        throw new Error(`Failed to submit email: ${response.status} ${response.statusText}`);
    }
}

class Showcase {
    constructor(element) {
        this.element = element;
        this.image = null;
        this.ocr = null;

        // setup ui behavior
        const tabButtonList = this.element.querySelectorAll(".tab-button");
        for (const tabButton of tabButtonList) {
            const eTextArea = this.element.querySelector("textarea");

            tabButton.addEventListener("click", () => {
                tabButtonList.forEach(btn => btn.classList.remove("active"));
                tabButton.classList.add("active");

                const type = tabButton.getAttribute("data-tab");
                if (this.ocr == null) {
                    eTextArea.value = "No data yet";
                } else if (type === "text") {
                    eTextArea.value = this.ocr.fullTextAnnotation.text;
                } else if (type === "json") {
                    eTextArea.value = JSON.stringify(this.ocr, null, 2);
                } else {
                    throw new Error("invalid tab button type");
                }
            })
        }
        tabButtonList.item(0).click();
    }

    getActiveTab() {
        for (const tabButton of this.element.querySelectorAll(".tab-button")) {
            if (tabButton.classList.contains("active")) {
                return tabButton;
            }
        }
    }

    setImage(_image) {
        const eImage = this.element.querySelector("img");
        this.image = _image;
        if (this.image == null) {
            eImage.src = "";
        } else if (typeof this.image === "string") {
            eImage.src = this.image;
        } else if (this.image instanceof File) {
            const eImage = this.element.querySelector('img');
            eImage.src = URL.createObjectURL(this.image);
        } else {
            throw new Error("Invalid type for image");
        }
    }

    getImage() {
        return this.image;
    }

    setOcr(_ocr) {
        this.ocr = _ocr;
        this.getActiveTab().click();
    }

}

function setErrorMessage(msg) {
    const e = document.getElementById("error-message");
    if (e != null) {
        e.innerText = msg;
        e.style.display = "block";
    }
}

function clearErrorMessage() {
    const e = document.getElementById("error-message");
    if (e != null) {
        e.innerText = "No errors";
        e.style.display = "none";
    }
}
