using System;
using System.IO;
using System.Drawing;
using System.Windows.Forms;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using TgaDecoderTest;

namespace Florensia_PAK_Editor
{
    public class PAKContentFile
    {
        private List<string> ImageExts = new List<string> { ".png", ".jpg", ".tga" };

        public byte[] FilenameRaw { get; set; }
        public string Filename { get; set; }
        public int Offset { get; set; }
        public int Length { get; set; }
        public byte[] Unknown1 { get; set; }
        public int Unknown2 { get; set; }
        public byte[] FileContent { get; set; }

        public PAKContentFile() { }

        public bool IsImage()
        {
            if ( ImageExts.Any(x => Filename.EndsWith(x)) )
            {
                return true;
            }
            return false;
        }

        public bool IsTGA()
        {
            if ( Filename.EndsWith(".tga") )
            {
                return true;
            }
            return false;
        }

        public string GetText()
        {
            return Encoding.UTF8.GetString(FileContent);
        }

        public Bitmap GetBitmapFromImage()
        {
            MemoryStream mStream = new MemoryStream();
            mStream.Write(FileContent, 0, Convert.ToInt32(FileContent.Length));
            Bitmap bm = new Bitmap(mStream, false);
            mStream.Dispose();
            return bm;
        }

        public Bitmap GetBitmapFromTGA()
        {
            return TgaDecoder.FromBinary(FileContent);
        }

        public void SaveTo(string basePath)
        {
            string path = Path.Combine(basePath, Filename);
            using (BinaryWriter writer = new BinaryWriter(File.OpenWrite(path)))
            {
                writer.Write(FileContent);
            }
        }
    }


    public class PAKFile
    {
        private string filename;

        private ListView listView;
        private Panel previewPanel;

        private List<PAKContentFile> contentFiles = new List<PAKContentFile>();

        private BinaryReader reader;
        private BinaryWriter writer;

        public PAKFile(string filename, ListView listView, Panel previewPanel)
        {
            this.filename = filename;
            this.listView = listView;
            this.previewPanel = previewPanel;

            reader = new BinaryReader(File.Open(filename, FileMode.Open, FileAccess.Read, FileShare.ReadWrite));
            writer = new BinaryWriter(File.Open(filename, FileMode.Open, FileAccess.Write, FileShare.ReadWrite));

            ReadFile();
            UpdateListView();
        }

        private void ReadFile()
        {
            reader.BaseStream.Position = 0;

            // Number of files packed into the .pak
            int fileCount = BitConverter.ToInt32(reader.ReadBytes(4), 0);

            for (int i = 0; i < fileCount; i++)
            {
                byte[] nameBytes = reader.ReadBytes(260);
                string name = NameBytesToString(nameBytes);
                int offset = BitConverter.ToInt32(reader.ReadBytes(4), 0);
                int length = BitConverter.ToInt32(reader.ReadBytes(4), 0);
                byte[] unknown1 = reader.ReadBytes(24);
                int unknown2 = BitConverter.ToInt32(reader.ReadBytes(4), 0);

                // Reads content
                long currentPos = reader.BaseStream.Position;
                reader.BaseStream.Position = offset;
                byte[] fileContent = reader.ReadBytes(length);

                // Resets Stream position after reading content
                reader.BaseStream.Position = currentPos;

                PAKContentFile pakFileContent = new PAKContentFile
                {
                    FilenameRaw = nameBytes,
                    Filename = name,
                    Offset = offset,
                    Length = length,
                    Unknown1 = unknown1,
                    Unknown2 = unknown2,
                    FileContent = fileContent,
                };

                contentFiles.Add(pakFileContent);
            }
        }

        private string NameBytesToString(byte[] nameBytes)
        {
            int i = nameBytes.Length - 1;
            while (nameBytes[i] == 0)
            {
                --i;
            }
            byte[] nameWithoutNulls = new byte[i + 1];
            Array.Copy(nameBytes, nameWithoutNulls, i + 1);

            return Encoding.UTF8.GetString(nameWithoutNulls);
        }

        private void UpdateListView()
        {
            listView.Items.Clear();

            // Iterating over all files and display them in the listview
            foreach (PAKContentFile file in contentFiles)
            {
                ListViewItem item = new ListViewItem(new string[] {
                    file.Filename,
                    file.Offset.ToString(),
                    file.Length.ToString(),
                });

                listView.Items.Add(item);
            }

            // Updates listview column widths
            listView.AutoResizeColumn(0, ColumnHeaderAutoResizeStyle.ColumnContent);
            listView.AutoResizeColumn(1, ColumnHeaderAutoResizeStyle.HeaderSize);
            listView.AutoResizeColumn(2, ColumnHeaderAutoResizeStyle.ColumnContent);
        }

        public void AddFile(string filepath)
        {
            // Decoded filename
            string filename = Path.GetFileName(filepath);
            // Filename as bytes
            byte[] filenameAsBytes = Encoding.UTF8.GetBytes(filename);

            // Filename as array with the size 260
            byte[] filenameByteArray = new byte[260];
            for (int j = 0; j < filenameAsBytes.Length; j++)
            {
                filenameByteArray[j] = filenameAsBytes[j];
            }

            // Deletes file(s) with the same filename as the one that is added
            for (int i = contentFiles.Count() - 1; i >= 0; i--)
            {
                if (contentFiles[i].Filename == filename)
                {
                    contentFiles.RemoveAt(i);
                }
            }
            // Reads the FileContent
            byte[] FileContent = File.ReadAllBytes(filepath);

            // Placeholder - gets updated in RewriteFiles later
            int offset = 0;

            // Length of the content
            int length = FileContent.Length;

            // random byte sequence - 24 bytes
            byte[] unknown1 = Encoding.UTF8.GetBytes("ABCDEFGHIJKLMNOPQRSTUVWX");

            // random int - 4 bytes
            int unknown2 = 42;

            PAKContentFile pakFileContentToAdd = new PAKContentFile
            {
                FilenameRaw = filenameByteArray,
                Filename = filename,
                Offset = offset,
                Length = length,
                Unknown1 = unknown1,
                Unknown2 = unknown2,
                FileContent = FileContent,
            };

            contentFiles.Add(pakFileContentToAdd);
        }

        public void DeleteFile(PAKContentFile file)
        /// Deletes given file
        {
            contentFiles.Remove(file);
            RewriteFile();
        }

        private void UpdateOffsets()
        /// Updates all offsets based on the file position in the List.
        /// Necessary because otherwise, if adding the same file over and over again,
        /// the file would increase in size.
        {
            int contentFilesLength = contentFiles.Count();

            for (int i = 0; i < contentFilesLength; i++)
            {
                PAKContentFile file = contentFiles[i];

                if (i == 0)
                {
                    file.Offset = 4 + (296 * contentFilesLength);
                }
                else
                {
                    PAKContentFile fileBefore = contentFiles[i - 1];
                    file.Offset = fileBefore.Offset + fileBefore.Length;
                }
            }
        }

        public void RewriteFile()
        /// Rewrites the .pak file based on the contentFiles list.
        {
            // Emptys file
            writer.BaseStream.SetLength(0);
            writer.Flush();

            // Writes number of files
            writer.Write(contentFiles.Count());

            UpdateOffsets();

            int index = 0;
            foreach (PAKContentFile file in contentFiles)
            {
                writer.BaseStream.Position = 4 + (296 * index);

                writer.Write(file.FilenameRaw);
                writer.Write(file.Offset);
                writer.Write(file.Length);
                writer.Write(file.Unknown1);
                writer.Write(file.Unknown2);

                // File content
                writer.BaseStream.Position = file.Offset;
                writer.Write(file.FileContent);

                index++;
            }

            writer.Flush();
            UpdateListView();
        }

        public void Close()
        /// Closes pak file
        {
            reader.Dispose();
            reader.Dispose();

            listView.Items.Clear();
        }

        public PAKContentFile GetFileByIndex(int index)
        {
            return contentFiles[index];
        }

        public List<PAKContentFile> GetAllFiles()
        {
            return contentFiles;
        }
    }
}
