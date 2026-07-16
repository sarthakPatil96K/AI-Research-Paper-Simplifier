import { useState } from "react";
import { uploadPDF } from "../services/uploadService";

function UploadPage() {

    const [file, setFile] = useState(null);

    const [loading, setLoading] = useState(false);

    const [response, setResponse] = useState(null);

    const [error, setError] = useState("");

    const handleUpload = async () => {

        if (!file) {
            alert("Please select a PDF");
            return;
        }

        setLoading(true);
        setError("");

        try {

            const data = await uploadPDF(file);

            setResponse(data);

        } catch (err) {

            setError(
                err.response?.data?.detail || "Upload Failed"
            );

        } finally {

            setLoading(false);

        }

    };

    return (

        <div
            style={{
                display: "flex",
                justifyContent: "center",
                marginTop: "100px",
            }}
        >

            <div>

                <h1>AI Research Paper Simplifier</h1>

                <input
                    type="file"
                    accept=".pdf"
                    onChange={(e) =>
                        setFile(e.target.files[0])
                    }
                />

                <br /><br />

                <button onClick={handleUpload}>

                    Upload PDF

                </button>

                <br /><br />

                {loading && <p>Uploading...</p>}

                {error && (
                    <p style={{ color: "red" }}>
                        {error}
                    </p>
                )}

                {response && (
                    <pre>
                        {JSON.stringify(response, null, 2)}
                    </pre>
                )}

            </div>

        </div>

    );

}

export default UploadPage;