document.getElementById("run-btn_2").addEventListener("click", function(event) {
    event.preventDefault(); // Предотвращаем стандартное поведение формы (редирект)

    const input = document.getElementById("upload-file_2");
    const files = input.files;

    const promisse_arr = []
    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        var formData = new FormData();
        formData.append("file", file);
        promisse_arr.push(fetch('/upload', {
            method: "POST",body: formData
          }
       ))
    }
    Promise.all(promisse_arr).then((result)=>{
        console.log(result)
        fetch('/process',{
            method: "POST"
        }).then((result)=>{
            document.getElementById('run-btn_2').innerHTML = '<i class="fas fa-check" style="font-size: 24px;"></i>';
            document.getElementById('status_2').innerText = "Download";
            document.getElementById('status_2').style.fontFamily = "Montserrat, sans-serif";
            document.getElementById('status_2').style.fontSize = "23px";
            document.getElementById('status_2').style.marginLeft = "5px";
            document.getElementById('run-btn_2').style.color = 'white';
        })


    })

});

