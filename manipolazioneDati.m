clear
close all

% Select folder and define invalid characters
sourceFolder = uigetdir;
[parentFolder, folderName] = fileparts(sourceFolder);

% WarningMode can be either 'auto' or 'man'. Use 'man' only if 'auto'
% doesnt work properly
warningMode = 'auto';

% List of characters that are not well recived by X-Zero
invalidCharacters = ["?", "²", "[", "]", string(char(8315))];

% Clean the folder name and create manipulated folder name
cleanFolderName = string(folderName);
for c = invalidCharacters
    cleanFolderName = replace(cleanFolderName, c, "");
end
manipulatedFolderName = cleanFolderName + "_Manipulated";
manipulatedFolderPath = fullfile(parentFolder, manipulatedFolderName);

% Copying files to the new folder name
disp("Copying files...")
copyfile(sourceFolder, manipulatedFolderPath)
cd(manipulatedFolderPath)
disp("All files copied.")

% Removing the invalid characters from the folder's name recursively
renameFolders(manipulatedFolderPath, invalidCharacters)

% Remove all the CurrentTestSpec.txt files
allTxtFiles = dir(fullfile('**', '*.txt'));
for i = 1:length(allTxtFiles)
    if startsWith(allTxtFiles(i).name, "Current")
        delete(fullfile(allTxtFiles(i).folder, allTxtFiles(i).name));
    end
end

disp("Invalid characters removed from the name of the directories.")

allTestFiles = dir('**/*.txt');
nTest = length(allTestFiles);

failedFiles = [];

% Main LOOP
for i = 1:nTest
    
    fullDirectory = fullfile(allTestFiles(i).folder, allTestFiles(i).name);
    relativeDirectory = (strrep(fullDirectory, cd, ''));
    
    % Check if i'm dealing with an actual test
    if ~testCheck(fullDirectory)
        disp([relativeDirectory, ' was not a test.'])
        delete(fullDirectory)
        continue
    end
    
    % Start of the exeption handling. If the program panics with a specific
    % file, the script will move on and notify the user about the error 
    % that occured with that file
    try
        
        % Import of the test file into a matlab table
        dataTest = importDati(fullDirectory);
        
        % Check if we are in an LSS
        [isLSS, LSSDirection] = LSSCheck2(fullDirectory);
        
        % Invert lateral distance
        dataTest.RelativeLateralDistance = dataTest.RelativeLateralDistance * -1;
        
        % TTC processing
        [newTime, startTestIndex] = ...
            TTCProcess(dataTest.TimeToCollisionlongitudinal, dataTest.Time, isLSS);
        
        % Warning processing
        dataTest.ADC6 = ...
            warningProcess(dataTest.ADC6, isLSS, newTime, startTestIndex, warningMode);
        
        % If the test is an LSS it adds the two columns at the end
        if isLSS
            [ApproachSpeed, DistToLine] = LSSProcessing(dataTest, fullDirectory, LSSDirection);
            dataTest.ApproachSpeed = ApproachSpeed;
            dataTest.DistToLine = DistToLine;
        end
        
        % Writing the new file and displaying the percentage of completition 
        tempDirectory = fullfile(allTestFiles(i).folder, 'temp.txt');
        writetable(dataTest, tempDirectory, 'Delimiter', '\t');
        
        tempFile = fopen(tempDirectory, 'rt');
        fileContent = fread(tempFile, '*char')';
        fclose(tempFile);
        delete(tempDirectory)
        
        fileContent = strsplit(fileContent, '\n');
        
        finalFile = fopen(fullDirectory, 'rt');
        
        for j = 1:4
            unitOfMeasure = fgetl(finalFile);
        end
        
        fclose(finalFile);
        
        finalFile = fopen(fullDirectory, 'wt');
        
        fprintf(finalFile, 'Anthony Best Dynamics Ltd\n');
        fprintf(finalFile, 'Points=\n');
        fprintf(finalFile, '%s\n', fileContent{1});
        
        fprintf(finalFile, unitOfMeasure);
        
        for j = 2:numel(fileContent)
            fprintf(finalFile, '%s\n', fileContent{j});  % Write each line followed by a newline
        end
        
        fclose('all');
       
        disp([sprintf('%.1f%%   ', i/nTest*100), relativeDirectory , ' was processed. '])
        
    catch e
        
        fprintf(2,'---------------------------------------------------------------------------------\n');
        fprintf(2,'There was an error: %s \n',e.message);
        disp([relativeDirectory , ' was NOT processed.']);
        fprintf(2,'---------------------------------------------------------------------------------\n');

        fclose('all');
        failedFiles = [failedFiles, "Error: "  + e.message, "File: " + relativeDirectory, ""];
       
        
        continue
        
        
    end
    
    
    
end


if ~isempty(failedFiles)
    logFile = fopen(fullfile(parentFolder, "error" + cleanFolderName + ".log"), 'wt');
    for i = 1:length(failedFiles)
        fprintf(logFile, '%s\n', failedFiles(i));
    end
    fclose('all');
end



fclose('all');

cd('..')



%% Functions

function [newTime, startTestIndex] = TTCProcess(TTCVector, TimeVector, isLSS)

    if isLSS == true || all(TTCVector == 0)
        newTime = [];
        startTestIndex = [];
        return
    end
    
    index = 1;
   
    while index < length(TTCVector) || isempty(index) == 1
    
        % Fills the first values of TTC if they are 0
        if TTCVector(1) == 0
            index = find(TTCVector > 0, 1);
            TTCVector(1:index) = TTCVector(index);
            index = 1;
        end
        
        
        % Tries to find the index where TTC = 0
        index = find(TTCVector(1:end) == 0, 1);
        
        % If there's no value for TTC == 0 breaks the loop
        if isempty(index) == 1
            break
        end
        
        % Define the "yStart" where you have the value just before TTC = 0
        % and its index
        yStart = [TTCVector(index-1) index-1];
        
        % Searches for the point after TTC = 0 were TTC > 0
        index = find(TTCVector(index:end) > 0, 1);
        % If there's none breaks the loop
        if isempty(index) == 1
            break
        end
        
        yEnd = [TTCVector(index + yStart(2)) index + yStart(2)];
        xEq = (yStart(2):yEnd(2)) - yStart(2);
        m = ((yEnd(1) - yStart(1) / (yEnd(2) - yStart(2))));
        TTCEq = m.*xEq + yStart(1);  
        TTCVector(yStart(2):yEnd(2)) = TTCEq;
           
    end
    
    startTestIndex = find(TTCVector < 4,1);
    newTime = TimeVector(startTestIndex:end) - 4 - TimeVector(startTestIndex);
   
end

function ADC6Out = warningProcess(ADC6Vector, isLSS, newTime, startTestIndex, warningMode)
% if we are processing an LSS we take the warning as empty
    if isLSS == true
        ADC6Out = zeros(size(ADC6Vector));
        return
    end
    
    warningThreshold = 1;
    
    switch warningMode
        case 'auto'
            DY = diff(ADC6Vector);
            indexFirstWarning = find(abs(DY(startTestIndex:end))>warningThreshold);   
            
        case 'man'
            figure,plot(newTime,ADC6Vector(startTestIndex:end)),grid on, hold on
            xlim([-4 0])
            xlabel('TTC [s]')
            title('FCW Warning')
            
            uiwait(msgbox('Zoom, than press any button and pick a trigger value (positive TTC for NaN)'))
            zoom on
            pause
            
            [xx,~] = ginput(1);
            indexFirstWarning = find(newTime >= xx, 1);
            close(gcf)          
            
    end
    
    ADC6Out = zeros(size(ADC6Vector));
    ADC6Out(startTestIndex + indexFirstWarning:end) = 5;    
    
end

function isTest = testCheck(filename)

    isTest = isfile(strrep(filename, '.txt', '.spec'));
 
end

% Deprecated function
function [isLSS,LSSDirection] = LSSCheck(filename)
    
    specFile = fopen((strrep(filename, '.txt', '.spec')), 'r');
    fgetl(specFile);
    descriptionLine = fgetl(specFile); 
    fclose(specFile);
    
    LSSIdentifiers = {'LKA','ELK','LDW'};
    isLSS = contains(descriptionLine,LSSIdentifiers);
    
    RightIdentifiers = {'Right', 'Road'};
    LeftIdentifiers = {'Left', 'Over', 'Onc'};
    
    if isLSS 
        
        if contains(descriptionLine, RightIdentifiers)
            LSSDirection = 'Right';     
        
        elseif contains(descriptionLine, LeftIdentifiers)
            LSSDirection = 'Left';
        else
           disp('No direction was found for the LSS test');            
        end
        
    else
        LSSDirection = [];
    end
    
 end

function [isLSS,LSSDirection] = LSSCheck2(filename)
    
    specFile = fopen((strrep(filename, '.txt', '.spec')), 'rt');
    
    fileContent = textscan(specFile, '%s', 'Delimiter', '\n');
    fclose(specFile);
    
    descriptionLine = fileContent{1}{2};
      
    LSSIdentifiers = {'LKA','ELK','LDW'};
    isLSS = contains(descriptionLine,LSSIdentifiers);
    
    RightIdentifiers = {'Right', 'Road'};
    LeftIdentifiers = {'Left', 'Over', 'Onc', 'CMOv'};
    
    if isLSS 
        
        if contains(descriptionLine, RightIdentifiers)
            LSSDirection = 'Right';     
        
        elseif contains(descriptionLine, LeftIdentifiers)
            LSSDirection = 'Left';
        else
           disp('No direction was found for the LSS test');            
        end
        
    else
        LSSDirection = [];
        fileContent{1}{2} = replace(fileContent{1}{2}, ' kph', 'VUT');
        
        specFile = fopen((strrep(filename, '.txt', '.spec')), 'wt');
        fprintf(specFile, '%s\n', fileContent{1}{:});
        fclose(specFile);
        
    end
    
end




function [ApproachSpeed, DistToLine] =  LSSProcessing(dataTable, filename, LSSDirection)

    [~, fileName, ext] = fileparts(filename);
    [LSSFolder, ~, ~] = fileparts(fileparts(filename));
    iniFiles = dir(fullfile(LSSFolder, '*.ini'));
        
    dt = dataTable.Time(2) - dataTable.Time(1);
    PositionVector = dataTable.ActualYfrontAxle;
        
    %low pass filter
    Wn=(10/50);
    [BBB,AAA] = butter(6,Wn,'low');
  
    zerosWithIni = length(iniFiles);
  
    switch zerosWithIni
        % old case with the manual zeros
        case 1
            iniPath = fullfile(iniFiles(1).folder, iniFiles(1).name);
            fid = fopen(iniPath, 'r');
            zeroOffset = str2double(fgetl(fid));
            fclose(fid);
            DistToLine = PositionVector - zeroOffset;
            derivPosition = diff(PositionVector)/dt;
            derivPosition = filtfilt(BBB,AAA,derivPosition);
            derivPosition = [0, derivPosition']';
            
            ApproachSpeed = derivPosition; 
            
        % new case with the automatic processing
        otherwise
            
            if ismember('LaneIsoLeftFromBPosLateral', dataTable.Properties.VariableNames) ||...
               ismember('LaneIsoRightFromCPosLateral', dataTable.Properties.VariableNames)
           
               distLeftToB = dataTable.LaneIsoLeftFromBPosLateral;
               distRightToC = dataTable.LaneIsoRightFromCPosLateral;
                
               if all(distLeftToB == 0) && all(distRightToC == 0)
                   disp('Missing information about the line offset.')
                   fprintf('%s was not correctly processed\n', strcat(fileName,ext))
                   ApproachSpeed = zeros(size(PositionVector));
                   DistToLine = zeros(size(PositionVector));
                   return
                             
               elseif all(distLeftToB == 0) && ~all(distRightToC == 0)
                   currentLine = distRightToC;
               elseif ~all(distLeftToB == 0) && all(distRightToC == 0)
                   currentLine = distLeftToB; 
               else
                  switch LSSDirection
                      case 'Right'
                          currentLine = distRightToC;
                      case 'Left'
                          currentLine = distLeftToB; 
                  end
               end
               
               if currentLine(1) == currentLine(2)
                   index = find(currentLine ~= currentLine(1), 1);
                   currentLine(1:index-1) = currentLine(index);                              
               end
               
               derivPosition = diff(currentLine)/dt;
               derivPosition = filtfilt(BBB,AAA,derivPosition);
               derivPosition = [0, derivPosition']';
               ApproachSpeed = derivPosition; 
               DistToLine = currentLine;
                      
            else
                disp('Missing information about the line offset.')
                fprintf('%s was not correctly processed\n', strcat(fileName,ext))
                ApproachSpeed = zeros(size(PositionVector));
                DistToLine = zeros(size(PositionVector));
                return
            end   
    end
  
end

function tableOut = importDati(filename)

    opts = detectImportOptions(filename);
   
    for i = 1:length(opts.VariableNames)
        opts = setvartype(opts, opts.VariableNames{i}, 'double');
    end
    
    opts.VariableNamesLine = 3;
    opts.DataLines = [4, Inf]; 
    
    tableOut = readtable(filename, opts, 'ReadVariableNames', true);    
  
    % remove underscores from the headers
    tableOut.Properties.VariableNames = ...
        strrep(tableOut.Properties.VariableNames, '_', '');
    
    %remove eventual NaN
    tableOut = tableOut(~any(isnan(tableOut{:,:}), 2), :);
    
 
end


function renameFolders(rootDir, invalidCharacters)
    % Get a list of all files and folders in this folder
    entries = dir(rootDir);
    
    % Filter out current and parent directory entries
    entries = entries(~ismember({entries.name}, {'.', '..'}));

    % Process folders first to go deep into structure before renaming
    for i = 1:length(entries)
        if entries(i).isdir
            % Recurse into subfolder
            subfolderPath = fullfile(rootDir, entries(i).name);
            renameFolders(subfolderPath, invalidCharacters);
        end
    end

    % Now rename folders after recursion (bottom-up renaming)
    for i = 1:length(entries)
        if entries(i).isdir
           
            newName = entries(i).name;
            oldName = newName;
            for c = invalidCharacters
                newName = replace(newName, c, "");
            end
            
            if ~strcmp(oldName, newName)
                oldPath = fullfile(rootDir, oldName);
                newPath = fullfile(rootDir, newName);
                if ~exist(newPath, 'dir')  % Avoid overwrite
                    movefile(oldPath, newPath);
                end
            end
        end
    end
end






