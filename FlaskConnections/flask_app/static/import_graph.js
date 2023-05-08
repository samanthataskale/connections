let random_identifier = 0;

window.onload = async function () {
    random_identifier = Math.floor(Math.random() * (1000000000 + 1));
}

// Import a graph
document.getElementById('import_graph_button').addEventListener('change', async (event) => {
    const file = event.target.files[0];
    graph = JSON.parse(await file.text())

    post_request = {
        "method": "POST",
        "headers": {"Content-Type": "application/json", 'X-CSRF-TOKEN': csrf_token},
        "body": JSON.stringify({"graph": graph, "identifier": random_identifier})
    }

    const names = graph["nxGraph"]["nodes"].filter(node => graph["name"].includes(node["id"])).map(node => node["label"]);
    console.log(names);

    var result = await fetch("/importjson", post_request);
    location.href = 'http://localhost:5000/graph?' + "names=" + encodeURIComponent(names) + '&ids=import,' + random_identifier
});