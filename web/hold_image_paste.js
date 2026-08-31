import { app } from "/scripts/app.js";
import { api } from "/scripts/api.js";


const NODE_TYPE = "SaintNeronaHoldImagePreview";
const UPLOAD_SUBFOLDER = "Saint-Nerona-Nodes";


function imageFileFromClipboard(clipboardData) {
    const item = Array.from(clipboardData?.items || []).find((entry) => entry.kind === "file" && entry.type.startsWith("image/"));
    const file = item?.getAsFile() || Array.from(clipboardData?.files || []).find((entry) => entry.type.startsWith("image/"));
    if (!file) {
        return null;
    }

    const subtype = (file.type.split("/")[1] || "png").replace("jpeg", "jpg");
    return new File([file], `saint-nerona-paste-${Date.now()}.${subtype}`, { type: file.type || "image/png" });
}


function splitInputPath(path) {
    const normalized = String(path || "").replaceAll("\\", "/");
    const separator = normalized.lastIndexOf("/");
    if (separator < 0) {
        return { filename: normalized, subfolder: "" };
    }
    return {
        filename: normalized.slice(separator + 1),
        subfolder: normalized.slice(0, separator),
    };
}


function showInputPreview(node, path) {
    if (!path) {
        return;
    }

    const { filename, subfolder } = splitInputPath(path);
    const preview = new Image();
    preview.onload = () => {
        node.setSizeForImage?.();
        node.setDirtyCanvas?.(true, true);
        app.graph.setDirtyCanvas(true, true);
    };
    preview.src = api.apiURL(`/view?filename=${encodeURIComponent(filename)}&subfolder=${encodeURIComponent(subfolder)}&type=input&rand=${Date.now()}`);
    node.imgs = [preview];
    node.imageIndex = 0;
}


function hideWidget(widget) {
    if (!widget) {
        return;
    }
    widget.hidden = true;
    widget.type = "converted-widget";
    widget.draw = () => {};
    widget.computeSize = () => [0, -4];
}


async function uploadClipboardImage(node, widget, file) {
    const body = new FormData();
    body.append("image", file);
    body.append("subfolder", UPLOAD_SUBFOLDER);
    body.append("overwrite", "false");

    const response = await api.fetchApi("/upload/image", { method: "POST", body });
    if (!response.ok) {
        throw new Error(`Image upload failed with status ${response.status}`);
    }

    const payload = await response.json();
    const path = payload.subfolder ? `${payload.subfolder}/${payload.name}` : payload.name;
    widget.value = path;
    widget.callback?.(path);
    showInputPreview(node, path);
}


app.registerExtension({
    name: "SaintNerona.HoldImagePaste",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== NODE_TYPE) {
            return;
        }

        const originalNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const result = originalNodeCreated?.apply(this, arguments);
            const node = this;
            const pastedImageWidget = node.widgets?.find((widget) => widget.name === "pasted_image");
            hideWidget(pastedImageWidget);

            const pasteHandler = async (event) => {
                if (!app.canvas.selected_nodes?.[node.id]) {
                    return;
                }

                const file = imageFileFromClipboard(event.clipboardData);
                if (!file) {
                    return;
                }

                event.preventDefault();
                event.stopImmediatePropagation();
                try {
                    await uploadClipboardImage(node, pastedImageWidget, file);
                } catch (error) {
                    console.error("[Saint Nerona] Could not paste image.", error);
                }
            };

            document.addEventListener("paste", pasteHandler, { capture: true });

            const originalRemoved = node.onRemoved;
            node.onRemoved = function () {
                document.removeEventListener("paste", pasteHandler, { capture: true });
                return originalRemoved?.apply(this, arguments);
            };

            setTimeout(() => showInputPreview(node, pastedImageWidget?.value), 0);
            return result;
        };
    },
});
