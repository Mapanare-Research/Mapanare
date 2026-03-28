import UIKit

/// Minimal iOS app embedding a Mapanare-compiled static library.
///
/// Build the .a:
///   mapanare build --target aarch64-apple-ios --lib -o libmapanare_app.a app.mn
///
/// Add libmapanare_app.a to your Xcode project and add the bridging header.
class ViewController: UIViewController {

    override func viewDidLoad() {
        super.viewDidLoad()

        let label = UILabel()
        label.text = String(cString: mn_greet("iOS"))
        label.font = .systemFont(ofSize: 24)
        label.textAlignment = .center
        label.frame = view.bounds
        view.addSubview(label)
    }
}

// C functions exported by the Mapanare static library
@_silgen_name("greet")
func mn_greet(_ name: UnsafePointer<CChar>) -> UnsafePointer<CChar>

@_silgen_name("compute_in_background")
func mn_compute(_ input: Int64) -> Int64
