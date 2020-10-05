<?php
if(array_key_exists("s", $_GET)) {
    $expr_get = $_GET["s"];
} else {
    $expr_get = "";
}

function search($expr) {
    $db = new SQLite3('socky.sqlite');

    $query = 'SELECT * FROM socky WHERE ';
    $num = is_numeric($expr);
    $len = strlen($expr);
    if($num && $len <= 2) {
        $query .= "field LIKE ?;";
        $stmt = $db->prepare($query);
        $stmt->bindValue(1, "$expr.%", SQLITE3_TEXT);
    } else if($num && $len == 4) {
        $query .= "year=?;";
        $stmt = $db->prepare($query);
        $stmt->bindValue(1, $expr, SQLITE3_TEXT);
    } else {
        $query .= 'authors LIKE ? OR title LIKE ? OR field LIKE ? OR description LIKE ?;';
        $stmt = $db->prepare($query);
        $stmt->bindValue(1, "%".$expr."%", SQLITE3_TEXT);
        $stmt->bindValue(2, "%".$expr."%", SQLITE3_TEXT);
        $stmt->bindValue(3, "%".$expr."%", SQLITE3_TEXT);
        $stmt->bindValue(4, "%".$expr."%", SQLITE3_TEXT);
    }

    $results = $stmt->execute();
    while ($row = $results->fetchArray()) {
        echo '<tr>';
        echo sprintf('<td style="white-space: nowrap;">%d. (%d)</td>', $row["season"], $row["year"]);
        echo sprintf('<td title="%s">%d</td>', $row["field"], intval($row["field"]));
        echo sprintf('<td>%d.</td>', $row["place"]);
        echo sprintf('<td><b>%s</b></td>', $row["title"]);
        echo sprintf('<td>%s</td>', $row["authors"]);
        echo sprintf('<td>%s</td>', $row["description"]);
        if($row["pdf"] == "") {
            echo '<td>nezveřejněno</td>';
        } else if($row["attachment"] != "") {
            echo sprintf('<td><a href="%s">práce</a><br><a href="%s">přílohy</a></td>', $row["pdf"], $row["attachment"]);
        } else {
            echo sprintf('<td><a href="%s">práce</a></td>', $row["pdf"]);
        }
        echo '</tr>';
    }
    $results->finalize();
    $stmt->close();
    $db->close();
}
?>
<html>
<head>
<meta content="text/html; charset=utf-8" http-equiv="Content-Type">
<title>SOČ hledač!</title>
<link rel="stylesheet" href="http://yui.yahooapis.com/pure/0.6.0/pure-min.css">
<style type="text/css">
td { vertical-align: top; }
</style>
</head>
<body>
<?php if($_GET["src"] == "sockari") { ?>
<a href="http://sockari.cz" style="margin: 20px;display:block;">Zpátky na sočkaři.cz...</a>
<?php } ?>
<center>
<h1 style="margin: 30px">Sočkohledač</h1>

<form class="pure-form" action="/">
    <input type="text" name="s" placeholder="Hledat..." value="<?php echo $expr_get; ?>">
    <input type="hidden" name="src" value="<?php echo $_GET["src"]; ?>">
    <button type="submit" class="pure-button">Hledat</button>
</form>

<?php
if($expr_get != "") {
?>
<table style="margin:30px" class="pure-table pure-table-bordered pure-table-stripped">
<thead>
<tr>
  <td>Ročník</td>
  <td>Obor</td>
  <td>Místo</td>
  <td>Název</td>
  <td>Autoři</td>
  <td>Popis</td>
  <td>Odkazy</td>
</tr>
</thead>
<?php search($_GET["s"]); ?>
</table>
<?php } ?>
</center>
</body>