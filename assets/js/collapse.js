$(document).ready(function() {
  $(".header").on("click", function() {
    const $header = $(this);
    const $content = $header.next();
    const collapseText = $header.data("collapse-text") || "Collapse";
    const expandText = $header.data("expand-text") || "Expand";

    $content.slideToggle(500, function() {
      $header.text($content.is(":visible") ? collapseText : expandText);
    });
  });
});
