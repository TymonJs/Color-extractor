function updateTextInput(val) {
    document.getElementById('range-label').value= val; 
  }
  function updateRange(obj) {
    document.getElementById('form-range').value= obj.value;
    if (this.value==""){
      document.getElementById('form-range').value = 1; 
    } 
    
  }
  function keepRange(val,max){
    var value = document.getElementById('range-label').value;
    if (value>max){
      document.getElementById('range-label').value= max; 
    }
    else if (value==""){
      document.getElementById('range-label').value= ""; 
    }
    else if (value<1 ){
      document.getElementById('range-label').value= 1; 
    }

  }
function updateFrame(frame,sizes){
    var frame = frame.value;
    if (frame){
      var x = (frame-1)*sizes['w'];
      document.getElementById('gif').style.backgroundPosition = -x +"px 0px";
    }
    else{
      document.getElementById('gif').style.backgroundPosition = "0px 0px";
    }
}
function myAlert(message){
  Swal(meesage)
}
function myAlert(message){
  Swal.fire({
  position: 'top-end',
  icon: 'success',
  title: message,
  showConfirmButton: false,
  timer: 1500
})
}