<?php
$mysql= new mysqli('localhost','root','12345678','x');


$manu=isset($_POST['manu']) ? $_POST['manu'] : '';
$name=$_POST['name'] ?? '';
$password=$_POST['password'] ?? '';
$signup=$_POST['signup'] ?? '';
$sign=$_POST['sign'] ?? '';
?>


<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document</title>
     
</head>
<body>
    <form method="post">
        <input type="submit" name="manu"  value="signup">
        <input type="submit" name="manu" value="sign">
    </form>
</body>
</html>

<?php
switch($manu){
    case 'signup':{
        ?>
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Document</title>
        </head>
        <body>
            <form method="post">
                <input type="hidden" name="manu" value="signup">
                <input type="text" name="name">
                <input type="password" name="password">
                <button type="submit" name="signup" value="signup">signup</button>
            </form>            
        </body>
        </html>
        <?php
        if($signup=="signup"){
            $sql="INSERT INTO x(name,password) VALUES('$name','$password')";
            $mysql->query($sql);
        }
        break;
    }
    case 'sign':{
        ?>
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Document</title>
        </head>
        <body>
            <form method="post">
                <input type="hidden" name="manu" value="sign">
                <input type="text" name="name" >
                <input type="password" name="password" >
                <button type="submit" name="sign" value="sign">sign</button>
            </form>
        </body>
        </html>
        <?php
        if($sign=="sign"){
            $sql="SELECT * FROM x WHERE name='$name' AND password='$password'";
            $res=$mysql->query($sql);
            if($res->num_rows>0){
                echo"pass";
            }else{
                echo"hello world";
            }
        }
    }
}
?>