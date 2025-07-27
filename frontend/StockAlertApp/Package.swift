// swift-tools-version: 5.9
// The swift-tools-version declares the minimum version of Swift required to build this package.

import PackageDescription

let package = Package(
    name: "StockAlertApp",
    platforms: [
        .iOS(.v16)
    ],
    products: [
        // Products define the executables and libraries a package produces, making them visible to other packages.
        .library(
            name: "StockAlertApp",
            targets: ["StockAlertApp"]),
    ],
    dependencies: [
        .package(url: "https://github.com/danielgindi/Charts.git", from: "5.0.0")
    ],
    targets: [
        // Targets are the basic building blocks of a package, defining a module or a test suite.
        // Targets can depend on other targets in this package and products from dependencies.
        .target(
            name: "StockAlertApp",
            dependencies: [
                .product(name: "Charts", package: "Charts")
            ]),
        .testTarget(
            name: "StockAlertAppTests",
            dependencies: ["StockAlertApp"]
        ),
    ]
)
