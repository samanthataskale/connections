//set basic handlers for functions that we generated solely ourselves
document.querySelector("#timeline").value = 100
document.querySelector("#timeline").disabled = true
document.querySelector("#timeline").addEventListener("input", timeline_handler);
document.getElementById("exportbtn").disabled = true



function timeline_handler(){
	let time = document.querySelector("#timeline").value;

    //calculate the current "date" as represented by the slider value
    let deltaDate = new Date( (time/100) * diffDate )
    let addedDate = firstSeenDate.getTime() + deltaDate.getTime() + (24 * 3600)
    let currDate = new Date(addedDate )
    document.getElementById("timelinecurrdate").innerHTML = "Displaying Connections from Before: " + currDate.toDateString()

    //do not set hidden directly, as that would interfere with the filter
    allEdges = edges.get({ returnType: "Object" });
    for (let edge in allEdges){
        let locFirstSeen = allEdges[edge].first_seen
        if (locFirstSeen){
            to_hide = new Date(locFirstSeen) > currDate
            allEdges[edge].hidden_time = to_hide
        }
    }

    setHidden()
    network.body.emitter.emit('_dataChanged')
    network.redraw()
}

//necessary variables in relatinon to date filtering
let firstSeen = "z"
let lastSeen = "0"
let firstSeenDate
let lastSeenDate
let diffDate

//random_identifier for "sessions"
let random_identifier=0;
//graph constants
let edges;
let nodes;
let allNodes;
let allEdges;
let filteredEdges = [];

var nodeColors;
var originalNodes;
var network;
var filter = {
    item : '',
    property : '',
    value : []
};

//functions that update the loading messages to keep users from getting bored
function editLoadingMessage(){
    const messages = ["Loading...", "Cooking up a Graph...", "Funny Loading Message Here..."]
    document.getElementById("loadmessage").innerHTML = messages[Math.floor(Math.random() * messages.length)];
}

function editExpandingMessage() {
    const messages = ["Expanding...", "Cooking up a Graph...", "Funny Expanding Message Here..."]
    document.getElementById("loadmessage").innerHTML = messages[Math.floor(Math.random() * messages.length)];
}

async function make_initial_graph(){
    document.getElementById("loadmessage").innerHTML = "Loading...";

    var handle = setInterval(editLoadingMessage, 3000);

	let data = { "dataids" : dataids, "identifier" :  random_identifier, "numNames" : names.length}
	post_request = {
		"method": "POST",
		"headers": {"Content-Type": "application/json", 'X-CSRF-TOKEN': csrf_token},
		"body": JSON.stringify({"data": data})
	}
	const result = await fetch("/buildgraph", post_request);
    const json = await result.json();
    clearInterval(handle)
    setTimeline(json[1])
    document.getElementById("loadmessage").innerHTML = " ";
    return json;
}

function setTimeline(edgesList){
    firstSeen = "z"
    lastSeen = "0"
    edgesList.forEach( x => {
        x.conns.forEach( y => {
            if (firstSeen > y.date){firstSeen = y.date}
            if (lastSeen < y.date){lastSeen = y.date}
        })
    });
    document.getElementById("timelinefirstseen").innerHTML = "First Seen: " + firstSeen;
    document.getElementById("timelinelastseen").innerHTML = "Last Seen: " + lastSeen;
    lastSeenDate = new Date(lastSeen)
    firstSeenDate = new Date(firstSeen)
    diffDate = lastSeenDate-firstSeenDate
    document.querySelector("#timeline").disabled = false;

}

function setHidden() {
    allEdges = edges.get({ returnType: "Object" });
    for (let edge in allEdges) {
        let edgeFiltered = (filteredEdges.find(x => x == edge) != undefined)
        let should_hide = allEdges[edge].hidden_time || edgeFiltered
        allEdges[edge].hidden = should_hide;
    }

    let updateArray = []
    for (let edgeId in allEdges) {
        if (allEdges.hasOwnProperty(edgeId)) {
            updateArray.push(allEdges[edgeId]);
        }
    }
    edges.update(updateArray);
}

function setupGraph(nodesList, edgesList){
    nodes = new vis.DataSet(nodesList);
    edges = new vis.DataSet(edgesList);
    nodeColors = {};
    allNodes = nodes.get({ returnType: "Object" });
    for (nodeId in allNodes) {
        nodeColors[nodeId] = allNodes[nodeId].color;
    }
    allEdges = edges.get({ returnType: "Object" });
    drawGraph()
}


function drawGraph() {

    var expandInProcess = false; // will ensure that expand operations don't interfere with one another.

    var container = document.getElementById('mynetwork');
    let data = {nodes: nodes, edges: edges};
    var options = {
        "configure": {
            "enabled": false
        },
        "edges": {
            "color": {
                "inherit": false
            },
            "smooth": {
                "enabled": true,
                "type": "dynamic"
            }
        },
        "interaction": {
            "dragNodes": true,
            "hideEdgesOnDrag": false,
            "hideNodesOnDrag": false,
            "selectable": true,
        },
        "physics": {
            "enabled": true,
            "barnesHut": {
                "avoidOverlap": 0.5,
                "centralGravity": 0.0,
                "damping": 1,
                "gravitationalConstant": -5000,
                "springConstant": 0.01,
                "springLength": 250
            },
            "stabilization": {
                "enabled": true,
                "fit": true,
                "iterations": 1000,
                "onlyDynamicEdges": false,
                "updateInterval": 50
            }
        },
        "layout":{
            "randomSeed": 10
        }
    };
    network = new vis.Network(container, data, options);

    network.stabilize();
    network.on('doubleClick', async function(properties){

        if (nodes.get(properties.nodes[0])['expanded']) {
            document.getElementById("loadmessage").innerHTML = "Already Expanded!";

        } else if (expandInProcess) {

            document.getElementById("loadmessage").innerHTML = "Please Wait until Expansion Completes";
            
        } else {

            expandInProcess = true;
            document.getElementById("loadmessage").innerHTML = "Expanding... ";
            var handle = setInterval(editExpandingMessage, 3000);

            var ids = properties.nodes;

            post_request = {
                "method": "POST",
                "headers": {"Content-Type": "application/json", 'X-CSRF-TOKEN': csrf_token},
                "body": JSON.stringify({'ids': nodes.get(ids), 'identifier': random_identifier})
            }

            var result = await fetch("/expandgraph", post_request);
            const json = await result.json();
            clearInterval(handle)
            setTimeline(json[1])
            setupGraph(...json)

            document.getElementById("loadmessage").innerHTML = " ";
            
            expandInProcess = false;
        }
    });
    
    network.on('hold', async function(properties){
        let nodeid = properties.nodes[0]
        let numEdges = 0
        for (let edgeid in allEdges){
            let edge = allEdges[edgeid]
            if (edge.from == nodeid || edge.to == nodeid){
                numEdges = numEdges + 1         
            }
        }

        if (numEdges == 1) {
            nodes.get(properties.nodes[0])['expanded'] = false
        }

        if (nodes.get(properties.nodes[0])['expanded']) {
            document.getElementById("loadmessage").innerHTML = "Not a leaf node!";

        } else {
            document.getElementById("loadmessage").innerHTML = "Deleting...";
            var ids = properties.nodes;
            post_request = {
                "method": "POST",
                "headers": {"Content-Type": "application/json", 'X-CSRF-TOKEN': csrf_token},
                "body": JSON.stringify({'ids': nodes.get(ids), 'identifier': random_identifier})
            }

            var result = await fetch("/deletenode", post_request);

            const json = await result.json();
            setTimeline(json[1])
            setupGraph(...json)
            document.getElementById("loadmessage").innerHTML = " ";
        }

    });
    
    network.on('click', function(properties){
        
        let ids = properties.nodes;
        let nodeid = properties.nodes[0]
        let node = nodes.get(ids)[0];
        if (!node){
            return;
        }
        let disp_string = "Node Selected: "
        node.auths.forEach( elem => {
            disp_string += elem.name + ", "
        })
        disp_string = disp_string.substring(0, disp_string.length - 2);

        document.getElementById("nodeselectedheader").innerHTML = disp_string
        let edges_str = "Shared Works:<br>"
        edges_str += "<ol>"
        const works = []
        paper_list = 1
        color_class = "blacktext"
        for (let edgeid in allEdges){
            let edge = allEdges[edgeid]
            switch (edge.color.toLowerCase()){
                case "#008000":
                    color_class = "greentext"
                    break
                case "#ff0000":
                    color_class = "redtext"
            }
            if (edge.from == nodeid || edge.to == nodeid){
                edge.conns.forEach(x => {
                    if (!(works.includes(x.name))) {
                        edges_str += `<li class=${color_class}>${x.name}</li>`
                        paper_list += 1
                        works.push(x.name)
                    }
                })
                
            }
        }
        edges_str += "</ol>"
        document.getElementById("nodeselectedbody").innerHTML = edges_str

    });

}

// Export a graph
async function exportGraph(){
    post_request = {
        "method": "POST",
        "headers": {"Content-Type": "application/json", 'X-CSRF-TOKEN': csrf_token},
        "body": JSON.stringify({'identifier': random_identifier})
    }

    var result = await fetch("/exportjson", post_request);
    const json = await result.json();
    let fileToSave = new Blob([JSON.stringify(json, null, 2)], {
        type: 'application/json'
    });
    
    var link = document.createElement("a");
    link.download = "graphData.json";
    link.href = URL.createObjectURL(fileToSave)
    link.click();
}

window.onload = async function () {
    //$('#welcomemodal').modal('show')
    let name_header = "Connections for " + names[0]
    if (names.length == 2){
        name_header += " and " + names[1]
    } else if (names.length > 2){
        for (let i = 1; i < names.length - 1; i ++){
            name_header += ", " + names[i]
        }
        name_header += ", and " + names[names.length - 1]
    }

  document.getElementById("namesheader").innerHTML = name_header

  let x = Math.floor(Math.random() * (1000000000 + 1));
  random_identifier = x;
  var [nodesList, edgesList] = await make_initial_graph();
  setupGraph(nodesList, edgesList);
  document.querySelector("#exportbtn").disabled = false
}

window.onbeforeunload = function(){
    post_request = {
        "method": "POST",
        "headers": {"Content-Type": "application/json", 'X-CSRF-TOKEN': csrf_token},
        "body": JSON.stringify({'rand': random_identifier})
    }

    fetch("/deletepkl", post_request);
}

async function expandGraph() {
    expandInProcess = true;

    document.getElementById("loadmessage").innerHTML = "Expanding...";

    let nonExpandedNodes = nodes.get({
        filter: function (node) {
          return node["expanded"] == false;
        }
    });

    post_request = {
        "method": "POST",
        "headers": {"Content-Type": "application/json", 'X-CSRF-TOKEN': csrf_token},
        "body": JSON.stringify({'ids': nonExpandedNodes, 'identifier': random_identifier})
    }

    var result = await fetch("/expandgraph", post_request);
    const json = await result.json();
    console.log("Got the json results!");
    setTimeline(json[1])
    setupGraph(...json)

    document.getElementById("loadmessage").innerHTML = " ";
    
    expandInProcess = false;
}