// 모달함수
var Btnclick = function (x, y) {
    x.onclick = function () {
        y.style.display = "block";
    }

}
var Spanclick = function (x, y) {
    x.onclick = function () {
        y.style.display = "none";
    }
}