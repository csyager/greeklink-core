/**
  * bootstrap-table - An extended table to integration with some of the most widely used CSS frameworks. (Supports Bootstrap, Semantic UI, Bulma, Material Design, Foundation)
  *
  * @version v1.19.1
  * @homepage https://bootstrap-table.com
  * @author wenzhixin <wenzhixin2010@gmail.com> (http://wenzhixin.net.cn/)
  * @license MIT
  */

 function sortTable(colNum, sortIconId, ...args) {
  /* sorts column number colNum (0 indexed), with a fontawesome sort icon
  with id = sortIconId.  If reverse=true sorts in reverse order.  All icons
  for other columns that should be reset when sorting on column number
  colNum are passed as additional arguments */
  var table, rows, switching, i, x, y, shouldSwitch, sortIcon, colHeader;
  table = document.getElementById("list_table");
  colHeader = table.rows[0].getElementsByTagName("TH")[colNum];
  sortIcon = document.getElementById(sortIconId);
  sortIcon.className = "fa fa-sort-alpha-asc";
  var nextArgs = setAttributesOfRelatedNodesAndGetNextArgs(args);
  colHeader.setAttribute("onclick", `reverseSort(${colNum}, '${sortIconId}', ${nextArgs});`);
  switching = true;
  /* Make a loop that will continue until
  no switching has been done: */
  while (switching) {
    // Start by saying: no switching is done:
    switching = false;
    rows = table.rows;
    /* Loop through all table rows (except the
    first, which contains table headers): */
    for (i = 2; i < (rows.length - 1); i++) {
      // Start by saying there should be no switching:
      shouldSwitch = false;
      /* Get the two elements you want to compare,
      one from current row and one from the next: */
      x = rows[i].getElementsByTagName("TD")[colNum];
      y = rows[i + 1].getElementsByTagName("TD")[colNum];
      // Check if the two rows should switch place:
      if (x.innerHTML.toLowerCase() > y.innerHTML.toLowerCase()) {
        // If so, mark as a switch and break the loop:
        shouldSwitch = true;
        break;
      }
    }
    if (shouldSwitch) {
      /* If a switch has been marked, make the switch
      and mark that a switch has been done: */
      rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
      switching = true;
    }
  }
}

function reverseSort(colNum, sortIconId, ...args) {
  var table, rows, sortIcon, colHeader;
  table = document.getElementById("list_table");
  colHeader = table.rows[0].getElementsByTagName("TH")[colNum];
  sortIcon = document.getElementById(sortIconId);
  var nextArgs = setAttributesOfRelatedNodesAndGetNextArgs(args);
  sortIcon.className = "fa fa-sort-alpha-desc";
  colHeader.setAttribute("onclick", `sortTable(${colNum}, '${sortIconId}', ${nextArgs});`);
  rows = table.rows;
  for (var i = 2; i < (rows.length); i++) {
    item = rows[i];
    item.parentNode.insertBefore(item, rows[2]);
  }
}

function setAttributesOfRelatedNodesAndGetNextArgs(relatedNodes) {
  var nextArgs = '';
  for (var i = 0; i<relatedNodes.length; i++) {
    var otherSortIconId = relatedNodes[i];
    nextArgs += '"' + otherSortIconId + '", ';
    var otherSortIcon = document.getElementById(otherSortIconId);
    otherSortIcon.className = "fa fa-sort";
  }
  
  return nextArgs
}