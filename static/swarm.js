const BEE_URL = 'http://localhost:1633';
const BEE_DEBUG_URL = 'http://localhost:1635';

function base64ToBlob(base64, contentType = '', sliceSize = 512) {
    const byteCharacters = atob(base64);
    const byteArrays = [];

    for (let offset = 0; offset < byteCharacters.length; offset += sliceSize) {
        const slice = byteCharacters.slice(offset, offset + sliceSize);

        const byteNumbers = new Array(slice.length);
        for (let i = 0; i < slice.length; i++) {
            byteNumbers[i] = slice.charCodeAt(i);
        }

        const byteArray = new Uint8Array(byteNumbers);
        byteArrays.push(byteArray);
    }
    return new Blob(byteArrays, {type: contentType});
}

function createFileFromBase64(base64, filename) {
    const blob = base64ToBlob(base64);
    return new File([blob], filename, {type: "image/png"});
}

async function getPostageStamp() {
    const beeDebug = new BeeJs.BeeDebug(BEE_DEBUG_URL);
    const stamps = await beeDebug.getAllPostageBatch();
    const stamp = stamps[0];
    return stamp.batchID;
}

async function upload(base64, description, poem, colors, metadata, generated) {
    const bee = new BeeJs.Bee(BEE_URL);

    const stamp = await getPostageStamp();

    const result = await bee.uploadFiles(stamp, [
        createFileFromBase64(base64, 'nft'),
        new File([description], "desc", {type: "text/plain"}),
        new File([poem], "poem", {type: "text/html"}),
        new File([colors], "colors", {type: "text/html"}),
        new File([metadata], "metadata", {type: "application/json"}),
        new File([generated], "gen", {type: "text/plain"}),
    ], {"indexDocument": "nft"})

    console.log(result.reference);
    return BEE_URL + '/bzz/' + result.reference + '/';
}