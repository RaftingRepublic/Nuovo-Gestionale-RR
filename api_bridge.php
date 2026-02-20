<?php
/**
 * PHP Bridge per FastAPI
 * Inoltra tutte le richieste da biblioshare.it/api/* a localhost:8001/api/*
 */

// Configurazione
$backend_url = 'http://localhost'; // Dummy host for unix socket
$socket_path = '/var/www/vhosts/raftingrepublic.com/subdomains/gestionale/httpdocs/socket/gunicorn.sock'; 
$api_prefix = '/api/v1'; // Prefisso API pubblico

// Configurazione
// $backend_url = 'http://127.0.0.1:8000'; // TCP (Disabilitato per problemi firewall??)
$backend_url = 'http://localhost'; // Dummy host for unix socket
$socket_path = '/var/www/vhosts/raftingrepublic.com/subdomains/gestionale/httpdocs/socket/gunicorn.sock'; 
$api_prefix = '/api/v1'; // Prefisso API pubblico

// Recupera l'URI richiesto
$request_uri = $_SERVER['REQUEST_URI'];

// Inizializza cURL
$ch = curl_init($backend_url . $request_uri);
curl_setopt($ch, CURLOPT_UNIX_SOCKET_PATH, $socket_path); // ATTIVATO: Usiamo Socket siccome TCP fallisce dal bridge

// Metodo HTTP
$method = $_SERVER['REQUEST_METHOD'];
curl_setopt($ch, CURLOPT_CUSTOMREQUEST, $method);

// Gestione CORS Preflight (OPTIONS)
// Se il browser chiede "Posso fare POST?", rispondiamo SÌ subito senza disturbare il backend
if ($method === 'OPTIONS') {
    header("Access-Control-Allow-Origin: *");
    header("Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS");
    header("Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With");
    header("HTTP/1.1 200 OK");
    exit;
}

// Headers standard
$headers = [];
foreach (getallheaders() as $name => $value) {
    if (strcasecmp($name, 'Host') == 0) continue;
    if (strcasecmp($name, 'Content-Type') == 0 && count($_FILES) > 0) continue; // Lascia che cURL gestisca il content-type per multipart
    if (strcasecmp($name, 'Content-Length') == 0 && count($_FILES) > 0) continue;
    $headers[] = "$name: $value";
}

// Aggiungi Headers Proxy standard (Fix per "Not Secure" e redirect sbagliati)
$proto = isset($_SERVER['HTTPS']) && $_SERVER['HTTPS'] === 'on' ? 'https' : 'http';
$headers[] = "X-Forwarded-Proto: $proto";
$headers[] = "X-Forwarded-For: " . $_SERVER['REMOTE_ADDR'];
$headers[] = "X-Forwarded-Host: " . $_SERVER['HTTP_HOST'];

curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);

// Gestione Body
if (count($_FILES) > 0) {
    // Gestione Multipart/Form-Data
    $post_data = $_POST; // Copia i campi testuali
    
    foreach ($_FILES as $key => $file) {
        // Supporto array di file (es. file[])
        if (is_array($file['tmp_name'])) {
            foreach ($file['tmp_name'] as $index => $tmp_name) {
                if (empty($tmp_name)) continue;
                $new_key = $key . "[$index]";
                $post_data[$new_key] = new CURLFile(
                    $tmp_name,
                    $file['type'][$index],
                    $file['name'][$index]
                );
            }
        } else {
            if (empty($file['tmp_name'])) continue;
            $post_data[$key] = new CURLFile(
                $file['tmp_name'],
                $file['type'],
                $file['name']
            );
        }
    }
    curl_setopt($ch, CURLOPT_POSTFIELDS, $post_data);
} elseif (!empty($_POST)) {
    // Post Form URL Encoded o multipart senza file (fallback rari)
    // Se Content-Type è json, $_POST è vuoto, quindi entra nel blocco successivo
    curl_setopt($ch, CURLOPT_POSTFIELDS, http_build_query($_POST));
} else {
    // Raw Body (JSON, XML, etc.)
    $input_data = file_get_contents('php://input');
    if (!empty($input_data)) {
        curl_setopt($ch, CURLOPT_POSTFIELDS, $input_data);
    }
}

// Opzioni cURL standard
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
curl_setopt($ch, CURLOPT_HEADER, true); // Vogliamo anche gli header di risposta

// Esegui richiesta
$response = curl_exec($ch);

if ($response === false) {
    http_response_code(502);
    header('Content-Type: application/json');
    echo json_encode(["detail" => "Bad Gateway: Errore connessione backend. " . curl_error($ch)]);
    exit;
}

// Separa Headers e Body nella risposta
$header_size = curl_getinfo($ch, CURLINFO_HEADER_SIZE);
$header_text = substr($response, 0, $header_size);
$body = substr($response, $header_size);

// Inoltra gli headers di risposta al client
foreach (explode("\r\n", $header_text) as $i => $line) {
    if ($i === 0) continue; // Salta status line
    if (!empty($line)) header($line);
}

// Imposta lo status code
http_response_code(curl_getinfo($ch, CURLINFO_HTTP_CODE));

// Stampa il body
echo $body;

curl_close($ch);
?>
