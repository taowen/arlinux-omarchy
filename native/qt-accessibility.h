#pragma once
#include <dlfcn.h>
#include <string.h>
#include <unistd.h>

/* Quickshell 0.3.1 replaces its temporary QCoreApplication with a
 * QGuiApplication. Qt's post-routine clears the accessibility factories when
 * that first application is destroyed, including Qt Quick's DSO registration.
 * Re-run Qt Quick's exported module initializer for each application startup.
 * qAddPreRoutine is Qt's supported application startup hook. Only this
 * product's Quickshell process installs it; CLI guests and Arlinux Arch do not.
 */
__attribute__((constructor))
static void omarchy_restore_quick_accessibility(void)
{
    const char *exe = bionicx_getenv("BIONICX_EXECFN");
    const char *name = exe ? strrchr(exe, '/') : NULL;
    if (!name || (strcmp(name + 1, "quickshell") && strcmp(name + 1, "qs")))
        return;
    void (*initialize)(void) = dlsym(RTLD_DEFAULT, "_Z23QQuick_initializeModulev");
    void (*add_pre_routine)(void (*)(void)) = dlsym(RTLD_DEFAULT, "_Z14qAddPreRoutinePFvvE");
    if (initialize && add_pre_routine) {
        add_pre_routine(initialize);
    } else {
        static const char error[] = "Omarchy: Qt Quick accessibility initialization hook unavailable\n";
        (void)write(STDERR_FILENO, error, sizeof(error) - 1);
    }
}
