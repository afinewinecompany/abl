{pkgs}: {
  deps = [
    pkgs.chromium
    pkgs.geckodriver
    pkgs.poppler_utils
    pkgs.glibcLocales
  ];
}
