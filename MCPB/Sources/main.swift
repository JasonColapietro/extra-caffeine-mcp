import Darwin
import Foundation
import Security

// Delegate stdio directly to the signed installed app. No shell, network, settings,
// GUI launch, tool filtering or additional protocol implementation lives here.
func fail(_ message: String) -> Never {
    FileHandle.standardError.write(Data(("Extra Caffeine adapter: " + message + "\n").utf8))
    exit(1)
}

let args = Array(CommandLine.arguments.dropFirst())
guard args.count == 2, args[0] == "--app", args[1].hasPrefix("/") else {
    fail("Usage: extra-caffeine-adapter --app /absolute/path/Extra Caffeine.app")
}
let appURL = URL(fileURLWithPath: args[1]).standardizedFileURL.resolvingSymlinksInPath()
guard appURL.pathExtension == "app",
      let infoData = try? Data(contentsOf: appURL.appendingPathComponent("Contents/Info.plist")),
      let info = (try? PropertyListSerialization.propertyList(from: infoData, format: nil)) as? [String: Any],
      let identifier = info["CFBundleIdentifier"] as? String,
      ["com.chesterwong.ExtraCaffeine", "com.chesterwong.ExtraCaffeine.Direct"].contains(identifier) else {
    fail("Select an installed Extra Caffeine or Extra Caffeine Direct app bundle.")
}
guard let version = info["CFBundleShortVersionString"] as? String,
      version.compare("1.2", options: .numeric) != .orderedAscending else {
    fail("MCP requires Extra Caffeine 1.2 or later. Update the selected app.")
}
guard let executable = info["CFBundleExecutable"] as? String,
      !executable.isEmpty, executable != ".", executable != "..", !executable.contains("/"), !executable.contains("\0") else {
    fail("The app has an invalid executable name. Reinstall the signed app.")
}
let executableURL = appURL.appendingPathComponent("Contents/MacOS").appendingPathComponent(executable).resolvingSymlinksInPath()
guard executableURL.path.hasPrefix(appURL.path + "/Contents/MacOS/"),
      FileManager.default.isExecutableFile(atPath: executableURL.path) else {
    fail("The app executable is missing or outside the app bundle. Reinstall the signed app.")
}
var code: SecStaticCode?
var requirement: SecRequirement?
let policy = "anchor apple generic and certificate leaf[subject.OU] = \"3GPMM2KM4R\" and identifier \"\(identifier)\""
guard SecStaticCodeCreateWithPath(appURL as CFURL, [], &code) == errSecSuccess,
      SecRequirementCreateWithString(policy as CFString, [], &requirement) == errSecSuccess,
      let code, let requirement,
      SecStaticCodeCheckValidity(code, SecCSFlags(rawValue: kSecCSStrictValidate | kSecCSCheckAllArchitectures), requirement) == errSecSuccess else {
    fail("App signature verification failed. Use an unmodified app signed by Chester Wong Consulting Ltd.")
}
// Let the installed protocol report closed/disabled state as a tool error.
// The stdio process supports discovery without launching the menu bar GUI.
// Launch Services enumeration can be stale or differ from the selected edition.
let strings = [executableURL.path, "--mcp"].map { strdup($0) }
var argv = strings + [nil]
execv(executableURL.path, &argv)
let error = String(cString: strerror(errno))
strings.forEach { free($0) }
fail("Could not start the app's MCP process: \(error)")
