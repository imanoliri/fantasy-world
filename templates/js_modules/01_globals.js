const svg = document.getElementById('mapSvg');
const tooltip = document.getElementById('tooltip');
const mapContainer = document.getElementById('mapContainer');
const table = document.getElementById('burgTable');
let selectedId = null;
let highlightedIds = [];

// These variables will be defined by data injection in the HTML itself
// let diplomacyMatrix = [];
// let stateNameIdMap = [];
