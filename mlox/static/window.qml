import QtQuick 2.8
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.3
import QtQuick.Dialogs 1.2

ApplicationWindow {
    id: mloxGui
    width: 800
    height: 600
    title: "mlox"
    visible: true

    FileDialog {
        id: openFileDialog
        nameFilters: ["INI files (*.ini)", "Text files (*.txt)", "All files (*)"]
        onAccepted: {
            python.open_file(fileUrl)
        }
    }

    menuBar: MenuBar {
        Menu {
            title: "File"
            MenuItem { text: "Open..."; onTriggered: openFileDialog.open() }
            MenuItem { text: "Reload";  onTriggered: python.reload() }
            MenuItem { text: "Debug";   onTriggered: python.show_debug_window() }
            MenuItem { text: "Exit";    onTriggered: Qt.quit() }
        }
        Menu {
            title: "Edit"
            MenuItem { text: "Copy Current Load Order";         onTriggered: {currentText.selectAll(); currentText.copy()} }
            MenuItem { text: "Copy Proposed Load Order";        onTriggered: {newText.selectAll(); newText.copy()} }
            MenuItem { text: "Paste a load order to analyze";   onTriggered: python.paste_handler() }
        }
        Menu {
            title: "Help"
            MenuItem { text: "About"; onTriggered: python.about_handler() }
        }
    }

    GridLayout {
        id: gridLayout
        rowSpacing: 3
        rows: 3
        columns: 2
        anchors.fill: parent
        Layout.fillHeight: true
        Layout.fillWidth: true

        GridLayout {
            id: topLayout
            height: 100
            Layout.fillHeight: true
            rows: 2
            columns: 2
            Layout.columnSpan: 2
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignLeft | Qt.AlignTop

            Text {
                id: statusLabel
                text: qsTr("Status")
                font.pixelSize: 20
                Layout.alignment: Qt.AlignLeft | Qt.AlignTop
                font.bold: true
                fontSizeMode: Text.FixedSize
                transformOrigin: Item.Center
            }

            Button {
                id: mloxButton
                text: ""
                Layout.fillHeight: false
                Layout.columnSpan: 1
                Layout.rowSpan: 2
                Layout.minimumHeight: 80
                Layout.minimumWidth: 80
                Layout.fillWidth: false
                anchors.right: parent.right
                anchors.rightMargin: 0

                Image {
                    id: image
                    width: 75
                    height: 75
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.verticalCenter: parent.verticalCenter
                    sourceSize.width: 75
                    sourceSize.height: 75
                    fillMode: Image.PreserveAspectFit
                    transformOrigin: Item.Center
                    visible: true
                    source: "image://static/mlox.gif"
                }
            }

            TextArea {
                id: statusText
                text: ""
                Layout.preferredHeight: 100
                Layout.alignment: Qt.AlignLeft | Qt.AlignTop
                Layout.fillWidth: true
                textFormat: TextEdit.RichText
                readOnly: true
            }
        }

        Text {
            id: messagesLabel
            text: qsTr("Messages")
            Layout.columnSpan: 2
            font.bold: true
            font.pixelSize: 20
        }

        TextArea {
            id: messagesText
            text: ""
            textFormat: TextEdit.RichText
            readOnly: true
            Layout.columnSpan: 2
            Layout.fillWidth: true
            Layout.fillHeight: true
            onLinkActivated: Qt.openUrlExternally(link)
        }

        Text {
            id: currentLabel
            text: qsTr("Current Load Order")
            Layout.alignment: Qt.AlignHCenter | Qt.AlignVCenter
            font.bold: true
            font.pixelSize: 20
        }

        Text {
            id: proposedLabel
            text: qsTr("Proposed Load Order")
            Layout.alignment: Qt.AlignHCenter | Qt.AlignVCenter
            font.bold: true
            font.pixelSize: 20
        }

        TextArea {
            id: currentText
            text: ""
            textFormat: TextEdit.RichText
            readOnly: true
            Layout.alignment: Qt.AlignHCenter | Qt.AlignTop
            Layout.minimumWidth: 380
            Layout.fillHeight: true
            Layout.fillWidth: true
        }

        TextArea {
            id: newText
            text: ""
            textFormat: TextEdit.RichText
            readOnly: true
            Layout.alignment: Qt.AlignHCenter | Qt.AlignTop
            Layout.minimumWidth: 380
            Layout.fillHeight: true
            Layout.fillWidth: true
        }

        Button {
            id: updateButton
            text: qsTr("Update Load Order")
//            font.bold: true
//            font.pixelSize: 40
            enabled: true
            Layout.minimumHeight: 60
            Layout.columnSpan: 2
            Layout.rowSpan: 1
            Layout.fillHeight: false
            Layout.fillWidth: true
        }
    }

    Connections {
        target: mloxButton
        onClicked: python.reload()
    }

    Connections {
        target: updateButton
        onClicked: python.commit()
    }

    Connections {
        target: python
        onEnable_updateButton: {updateButton.enabled = is_enabled}
        onSet_status: {statusText.text = text}
        onSet_message: {messagesText.text = text}
        onSet_new: {newText.text = text}
        onSet_old: {currentText.text = text}
    }

}
