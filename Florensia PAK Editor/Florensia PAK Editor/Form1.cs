using System;
using System.IO;
using System.Drawing;
using System.Windows.Forms;

namespace Florensia_PAK_Editor
{
    public partial class Form1 : Form
    {

        public PAKFile pak;

        public Form1()
        {
            InitializeComponent();
            string[] args = Environment.GetCommandLineArgs();
            
            if (args.Length > 1) // args[0] = file name of executing program
            {
                // arg 2 = filename for pak to open
                OpenPAK(args[1]);
            }
        }

        private void openToolStripMenuItem_Click(object sender, EventArgs e)
        {
            // Closes pak if open
            if (pak != null)
                ClosePAK();


            // Gets path and opens pak
            if (selectPakFileDialog.ShowDialog() == DialogResult.OK)
            {
                OpenPAK(selectPakFileDialog.FileName);
            }

        }

        private void closeToolStripMenuItem_Click(object sender, EventArgs e)
        {
            ClosePAK();
            Text = "Florensia PAK Editor";
        }

        private void exitToolStripMenuItem_Click(object sender, EventArgs e)
        {
            Application.Exit();
        }

        private void OpenPAK(string filename)
        {
            pak = new PAKFile(filename, filesListView, previewPanel);

            closeToolStripMenuItem.Enabled = true;
            Text = string.Format("Florensia PAK Editor - {0}", Path.GetFileName(filename));

        }

        private void ClosePAK()
        {
            pak.Close();
            closeToolStripMenuItem.Enabled = false;
        }

        private void filesListView_SelectedIndexChanged(object sender, EventArgs e)
        {
            previewPanel.Controls.Clear(); // clears preview

            if (filesListView.FocusedItem == null)
                return;

            int index = filesListView.FocusedItem.Index;
            PAKContentFile file = pak.GetFileByIndex(index);

            if (file.IsImage())
            {
                Bitmap bmp;
                Color bgColor;

                if (file.IsTGA())
                {
                    bmp = file.GetBitmapFromTGA();
                    bgColor = Color.Black;
                }
                else
                {
                    bmp = file.GetBitmapFromImage();
                    bgColor = Color.Transparent;
                }

                PictureBox box = new PictureBox
                {
                    Image = bmp,
                    SizeMode = PictureBoxSizeMode.AutoSize,
                    BackColor = bgColor,
                };
                previewPanel.Controls.Add(box);
            }
            else
            {
                TextBox textBox = new TextBox
                {
                    Text = file.GetText(),
                    Dock = DockStyle.Fill,
                    Multiline = true,
                    ScrollBars = ScrollBars.Both,
                    WordWrap = true,
                    ReadOnly = true,
                };
                previewPanel.Controls.Add(textBox);
            }
        }

        private void filesListView_MouseClick(object sender, MouseEventArgs e)
        {
            if (e.Button == MouseButtons.Right)
            {
                if (filesListView.FocusedItem.Bounds.Contains(e.Location))
                {
                    listViewContextMenu.Show(Cursor.Position);
                }
            }
        }

        private void selectedToolStripMenuItem_Click(object sender, EventArgs e)
        {
            if (selectFolderDialog.ShowDialog() == DialogResult.OK)
            {
                foreach (ListViewItem item in filesListView.SelectedItems)
                {
                    PAKContentFile file = pak.GetFileByIndex(item.Index);
                    file.SaveTo(selectFolderDialog.SelectedPath);
                }
            }

        }

        private void allToolStripMenuItem_Click(object sender, EventArgs e)
        {
            if (selectFolderDialog.ShowDialog() == DialogResult.OK)
            {
                foreach (PAKContentFile file in pak.GetAllFiles())
                {
                    file.SaveTo(selectFolderDialog.SelectedPath);
                }
            }
        }

        private void filesListView_DragEnter(object sender, DragEventArgs e)
        {
            e.Effect = DragDropEffects.Copy;
        }

        private void filesListView_DragDrop(object sender, DragEventArgs e)
        {
            string[] fileList = (string[])e.Data.GetData(DataFormats.FileDrop, false);

            foreach (string filename in fileList)
            {
                pak.AddFile(filename);
            }
            pak.RewriteFile();
        }

        private void deleteToolStripMenuItem_Click(object sender, EventArgs e)
        {
            int index = filesListView.FocusedItem.Index;
            PAKContentFile file = pak.GetFileByIndex(index);
            pak.DeleteFile(file);
        }
    }
}
