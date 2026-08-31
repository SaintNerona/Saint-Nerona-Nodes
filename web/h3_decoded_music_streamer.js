// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 Saint Nerona contributors
// Dynamic-socket behavior adapted from ComfyUI-H3-Motion-Context-MultiRef.

import { app } from "/scripts/app.js";


const NODE_TYPE = "SaintNeronaH3DecodedMusicVideoStreamer";
const PREFIX = "clip_";
const MAX_INPUTS = 64;
const DEFAULT_INPUTS = 2;


function inputCountWidget(node) {
    return node?.widgets?.find((widget) => widget.name === "input_count") ?? null;
}


function desiredInputCount(node) {
    const raw = Number(inputCountWidget(node)?.value ?? DEFAULT_INPUTS);
    if (!Number.isFinite(raw)) {
        return DEFAULT_INPUTS;
    }
    return Math.max(2, Math.min(MAX_INPUTS, Math.trunc(raw)));
}


function clipNumber(input) {
    const name = String(input?.name ?? "");
    if (!name.startsWith(PREFIX)) {
        return null;
    }
    const suffix = name.slice(PREFIX.length);
    return /^\d+$/.test(suffix) ? Number(suffix) : null;
}


function reconcileClipInputs(node) {
    if (!Array.isArray(node?.inputs)) {
        return;
    }
    const wanted = desiredInputCount(node);

    // Remove only excess sockets from the end; lower-numbered song-timeline
    // links keep both their identity and their ordering.
    for (let index = node.inputs.length - 1; index >= 0; index -= 1) {
        const number = clipNumber(node.inputs[index]);
        if (number != null && number > wanted) {
            if (node.inputs[index]?.link != null) {
                node.disconnectInput?.(index);
            }
            node.removeInput(index);
        }
    }

    const present = new Set(
        node.inputs.map((input) => clipNumber(input)).filter((number) => number != null),
    );
    for (let number = 1; number <= wanted; number += 1) {
        if (!present.has(number)) {
            node.addInput(`${PREFIX}${number}`, "LATENT", { shape: 7 });
        }
    }

    node.setSize?.(node.computeSize?.() ?? node.size);
    node.setDirtyCanvas?.(true, true);
}


function ensureUpdateButton(node) {
    if (node._saintNeronaH3UpdateInputsButton) {
        return;
    }
    const button = node.addWidget?.(
        "button",
        "Update inputs",
        null,
        () => reconcileClipInputs(node),
    );
    if (button) {
        button.serialize = false;
        button.options ??= {};
        button.options.serialize = false;
        node._saintNeronaH3UpdateInputsButton = button;
    }
}


app.registerExtension({
    name: "SaintNerona.H3DecodedMusicVideoStreamer",

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData?.name !== NODE_TYPE) {
            return;
        }

        const originalCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function (...args) {
            const result = originalCreated?.apply(this, args);
            ensureUpdateButton(this);
            reconcileClipInputs(this);
            return result;
        };

        const originalConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function (info, ...args) {
            const result = originalConfigure?.call(this, info, ...args);
            // Reconcile synchronously so ComfyUI can restore saved links onto
            // the matching numbered sockets in its normal configuration pass.
            ensureUpdateButton(this);
            reconcileClipInputs(this);
            return result;
        };
    },
});
